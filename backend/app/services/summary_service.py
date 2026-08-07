"""Final-output generation: a structured summary and insights for a session.

Consumes the stored Q&A record and asks the LLM for an evaluation grounded in
the candidate's actual answers. A deterministic fallback guarantees the endpoint
always returns a usable summary even if the model call fails.
"""

from __future__ import annotations

import logging

from ..models import InterviewSession
from ..roles import get_role
from ..schemas import SessionInsights
from . import llm

logger = logging.getLogger(__name__)


_SUMMARY_PROMPT = """You are a senior interviewer writing a screening summary for a \
"{role_label}" candidate. Evaluate ONLY on the basis of the transcript below — do \
not invent facts. Be fair, specific, and concise.

CANDIDATE: {candidate_name}
RESUME SUMMARY: {experience_summary}

TRANSCRIPT (question, topic, difficulty, and the candidate's answer):
{transcript}

Return JSON with exactly these keys:
- "overall_assessment": 3-4 sentence assessment of the candidate's performance
- "strengths": array of specific strengths shown (max 5)
- "areas_to_improve": array of specific gaps or weaker areas (max 5)
- "recommendation": one of "Strong Hire", "Hire", "Lean Hire", "No Hire", "Insufficient Signal"
- "score": integer 0-100 reflecting overall interview performance
"""


def generate_insights(session: InterviewSession) -> SessionInsights:
    role = get_role(session.role)
    transcript = _format_transcript(session)

    if not transcript.strip():
        return SessionInsights(
            overall_assessment="No answers were recorded for this session.",
            recommendation="Insufficient Signal",
        )

    prompt = _SUMMARY_PROMPT.format(
        role_label=role.label,
        candidate_name=session.candidate_name,
        experience_summary=(session.resume_profile or {}).get(
            "experience_summary", "(not provided)"
        ),
        transcript=transcript,
    )
    try:
        data = llm.generate_json(prompt, temperature=0.3)
        return SessionInsights(
            overall_assessment=str(data.get("overall_assessment", "")).strip(),
            strengths=_str_list(data.get("strengths"))[:5],
            areas_to_improve=_str_list(data.get("areas_to_improve"))[:5],
            recommendation=str(data.get("recommendation", "")).strip()
            or "Insufficient Signal",
            score=_clamp_score(data.get("score")),
        )
    except Exception as exc:
        logger.warning("Insight generation failed, using fallback: %s", exc)
        answered = sum(1 for qa in session.qa_pairs if qa.answer)
        return SessionInsights(
            overall_assessment=(
                f"The candidate answered {answered} of "
                f"{len(session.qa_pairs)} questions for the {role.label} role. "
                "Automated evaluation was unavailable; please review the "
                "transcript manually."
            ),
            recommendation="Insufficient Signal",
        )


def _format_transcript(session: InterviewSession) -> str:
    lines = []
    for i, qa in enumerate(session.qa_pairs, start=1):
        if not qa.answer:
            continue
        lines.append(
            f"Q{i} [{qa.topic} | {qa.difficulty}]: {qa.question}\n"
            f"Answer: {qa.answer}"
        )
    return "\n\n".join(lines)


def _str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()]


def _clamp_score(value) -> int | None:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return None
