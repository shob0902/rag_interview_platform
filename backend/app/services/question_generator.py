"""Question generation — the "G" in RAG.

Generates one interview question at a time, grounded in the retrieved knowledge
-base context and tailored to the candidate. Generating incrementally (rather
than all questions up front) is what enables **adaptivity**: each new question
is conditioned on the questions already asked and the candidate's most recent
answer, so the interview can probe deeper or pivot based on how they responded.

Every generated question carries a ``rationale`` and the ``context_indices`` it
drew from, preserving full traceability of *why* and *from what* it was created.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ..schemas import ResumeProfile
from ..roles import get_role
from . import llm
from .vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class GeneratedQuestion:
    question: str
    topic: str
    difficulty: str
    rationale: str
    context_indices: list[int]


_GROUNDED_RULES = """You MUST ground every question in the provided KNOWLEDGE BASE \
CONTEXT (extracted from the role's authoritative textbook). Do not ask generic or \
template questions; the question must test understanding of a concept present in \
the context, connected to the candidate's background."""

# Used when retrieval returned nothing: a custom role with no applicable
# knowledge base, or a preset role whose knowledge base hasn't been ingested.
_UNGROUNDED_RULES = """No knowledge base passages are available for this role. \
Base every question on well-established, widely taught concepts and practices that \
are core to the "{role_label}" role. Do not ask trivia, generic or template \
questions; the question must test real understanding, connected to the candidate's \
background. Return an empty "context_indices" array."""

_SYSTEM_PROMPT = """You are a senior technical interviewer conducting a live, \
role-specific screening interview for the role of "{role_label}".
Role focus: {role_description}

{grounding_rules}

CANDIDATE PROFILE
- Seniority: {seniority}
- Skills: {skills}
- Technologies: {technologies}
- Domains: {domains}
- Summary: {experience_summary}

Guidance on difficulty (driven by the resume): calibrate to the candidate's \
seniority and stated depth. A senior candidate strong in a domain should get a \
harder, more conceptual question in that domain; a junior candidate should get a \
foundational one. Vary topics across the interview.

KNOWLEDGE BASE CONTEXT (each item is a retrieved chunk you may use):
{context_block}

QUESTIONS ALREADY ASKED (do not repeat or closely paraphrase these):
{asked_block}

{followup_block}

Produce the NEXT single interview question. Return JSON with exactly these keys:
- "question": the question text (one focused question, may include a short scenario)
- "topic": short topic label (e.g. "Bias-Variance Tradeoff")
- "difficulty": one of "easy", "medium", "hard"
- "rationale": one sentence on why this question suits THIS candidate and which concept it tests
- "context_indices": array of integer indices (from the context list above) that the question is grounded in
"""


def generate_question(
    *,
    role_id: str,
    profile: ResumeProfile,
    context: list[RetrievedChunk],
    asked_questions: list[str],
    last_question: str | None = None,
    last_answer: str | None = None,
) -> GeneratedQuestion:
    """Generate the next grounded, adaptive interview question."""

    role = get_role(role_id)

    context_block = _format_context(context)
    asked_block = (
        "\n".join(f"- {q}" for q in asked_questions) if asked_questions else "(none yet)"
    )
    followup_block = _format_followup(last_question, last_answer)

    grounding_rules = (
        _GROUNDED_RULES
        if context
        else _UNGROUNDED_RULES.format(role_label=role.label)
    )

    prompt = _SYSTEM_PROMPT.format(
        grounding_rules=grounding_rules,
        role_label=role.label,
        role_description=role.description,
        seniority=profile.seniority,
        skills=", ".join(profile.skills) or "(not specified)",
        technologies=", ".join(profile.technologies) or "(not specified)",
        domains=", ".join(profile.domains) or "(not specified)",
        experience_summary=profile.experience_summary or "(not provided)",
        context_block=context_block,
        asked_block=asked_block,
        followup_block=followup_block,
    )

    data = llm.generate_json(prompt, temperature=0.6)

    indices = [
        i for i in _as_int_list(data.get("context_indices")) if 0 <= i < len(context)
    ]
    return GeneratedQuestion(
        question=str(data.get("question", "")).strip(),
        topic=str(data.get("topic", "General")).strip() or "General",
        difficulty=_norm_difficulty(data.get("difficulty")),
        rationale=str(data.get("rationale", "")).strip(),
        context_indices=indices,
    )


def _format_context(context: list[RetrievedChunk]) -> str:
    if not context:
        return "(no context retrieved — ask a foundational role question)"
    lines = []
    for i, chunk in enumerate(context):
        snippet = chunk.text.strip().replace("\n", " ")
        if len(snippet) > 700:
            snippet = snippet[:700] + "…"
        lines.append(f"[{i}] (source: {chunk.source}) {snippet}")
    return "\n\n".join(lines)


def _format_followup(last_question: str | None, last_answer: str | None) -> str:
    if not last_answer:
        return ""
    return (
        "MOST RECENT EXCHANGE (use this to adapt — probe deeper if the answer was "
        "strong, or pivot/clarify if it was weak or incomplete):\n"
        f"Q: {last_question}\nA: {last_answer}\n"
    )


def _as_int_list(value) -> list[int]:
    if not isinstance(value, list):
        return []
    out = []
    for v in value:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return out


def _norm_difficulty(value) -> str:
    v = str(value or "").lower()
    return v if v in {"easy", "medium", "hard"} else "medium"
