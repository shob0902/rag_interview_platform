"""Retrieval mechanism — the "R" in RAG.

Given the selected role and the candidate's resume profile, this module:

1. **Constructs queries dynamically** from the resume (skills, technologies,
   domains) combined with the role focus, rather than using a single static
   query. This is what makes retrieval *resume-driven*: a candidate strong in
   NLP pulls different chunks than one strong in reinforcement learning.
2. **Retrieves** the most relevant chunks per query from the role's knowledge
   base and **fuses** the per-query results, de-duplicating and keeping the
   highest similarity score for any chunk that surfaces for multiple queries.

The fused, ranked chunks become the grounded context for question generation.

For a custom (typed-in) role there is no knowledge base of its own, so
``knowledge_base_for`` asks the LLM once whether an existing one is core to that
role. Similarity scores alone can't decide this: an unrelated role such as
"Mechanical Engineer" scores about as high against the ML textbook as a related
one does. When nothing applies, retrieval returns no chunks and questions are
generated from the role's core concepts instead.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from ..config import get_settings
from ..roles import get_role, list_roles
from ..schemas import ResumeProfile
from . import gemini_client, llm, vector_store
from .vector_store import RetrievedChunk

logger = logging.getLogger(__name__)
settings = get_settings()


_KB_MATCH_PROMPT = """You are deciding whether an existing knowledge base should \
be used to write screening-interview questions for the role "{role_label}".

Available knowledge bases:
{options}

Choose a knowledge base ONLY if its subject matter is core to this role, i.e. \
material an interviewer for this role would genuinely test. Superficial or \
adjacent overlap does not count. For example, a machine-learning textbook IS \
relevant for "NLP Engineer" or "Machine Learning Researcher", but NOT for \
"Frontend Developer", "Accountant" or "Mechanical Engineer".

Return JSON with exactly one key: {{"knowledge_base": "<id>"}} using an id from \
the list above, or {{"knowledge_base": null}} if none is core to the role.
"""


def knowledge_base_for(role_id: str) -> str | None:
    """Return the knowledge-base role id to retrieve from, or None.

    Preset roles use their own knowledge base. For custom roles the LLM's
    decision is cached per role name; failures aren't cached, so a transient
    LLM error is retried on the next question.
    """

    role = get_role(role_id)
    if not role.custom:
        return role.id
    try:
        return _match_knowledge_base(role.label.lower())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Knowledge-base match failed for %r: %s", role.label, exc)
        return None


@lru_cache(maxsize=256)
def _match_knowledge_base(role_label: str) -> str | None:
    candidates = [r for r in list_roles() if vector_store.count(r.id) > 0]
    if not candidates:
        return None

    options = "\n".join(
        f'- "{r.id}": {r.label} ({r.description})' for r in candidates
    )
    data = llm.generate_json(
        _KB_MATCH_PROMPT.format(role_label=role_label, options=options),
        temperature=0.0,
    )
    choice = data.get("knowledge_base") if isinstance(data, dict) else None
    match = choice if choice in {r.id for r in candidates} else None
    logger.info("Knowledge base for custom role %r: %s", role_label, match)
    return match


def build_queries(*, profile: ResumeProfile, role_id: str) -> list[str]:
    """Derive a handful of focused retrieval queries from resume + role."""

    role = get_role(role_id)
    queries: list[str] = []

    # Pair each salient resume signal with the role focus so retrieval targets
    # material that is both role-relevant and grounded in the candidate's CV.
    signals = _dedup(profile.domains + profile.skills + profile.technologies)
    for signal in signals[:5]:
        queries.append(f"{role.label} concepts related to {signal}")

    # Always include at least one role-level query so we retrieve core material
    # even for a sparse resume.
    queries.append(f"Core {role.label} fundamentals: {role.description}")

    return _dedup(queries)


def retrieve_context(
    *,
    profile: ResumeProfile,
    role_id: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Run all queries and return fused, de-duplicated, ranked chunks."""

    top_k = top_k or settings.retrieval_top_k
    kb_role = knowledge_base_for(role_id)
    if kb_role is None:
        return []
    queries = build_queries(profile=profile, role_id=role_id)

    # chunk_index+source uniquely identifies a chunk; keep the best score seen.
    best: dict[tuple[str, int], RetrievedChunk] = {}
    for q in queries:
        try:
            embedding = gemini_client.embed_query(q)
        except Exception as exc:
            logger.warning("Embedding query failed (%s): %s", q, exc)
            continue
        for chunk in vector_store.query(
            query_embedding=embedding, role=kb_role, top_k=top_k
        ):
            key = (chunk.source, chunk.chunk_index)
            if key not in best or chunk.score > best[key].score:
                best[key] = chunk

    ranked = sorted(best.values(), key=lambda c: c.score, reverse=True)
    return ranked[:top_k]


def _dedup(items: list[str]) -> list[str]:
    seen, out = set(), []
    for item in items:
        key = item.strip().lower()
        if item.strip() and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out
