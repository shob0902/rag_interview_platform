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
"""

from __future__ import annotations

import logging

from ..config import get_settings
from ..roles import get_role
from ..schemas import ResumeProfile
from . import gemini_client, vector_store
from .vector_store import RetrievedChunk

logger = logging.getLogger(__name__)
settings = get_settings()


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
            query_embedding=embedding, role=role_id, top_k=top_k
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
