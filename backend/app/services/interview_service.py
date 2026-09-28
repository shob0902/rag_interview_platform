"""Interview orchestration — the heart of the backend business logic.

Coordinates the full pipeline for a session and owns the interview lifecycle:

    resume -> profile -> retrieve context -> generate question -> store
           -> collect answer -> (adapt) generate next -> ... -> summarise

The web layer (routers) stays thin: it validates input and delegates to the
functions here, which are the single place that knows how a session advances.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from ..config import get_settings
from ..models import InterviewSession, QAPair
from ..roles import get_role
from ..schemas import ResumeProfile
from . import question_generator, resume_parser, retrieval, summary_service

logger = logging.getLogger(__name__)
settings = get_settings()


class InterviewError(Exception):
    """Raised for expected, user-facing interview flow errors."""


# --------------------------------------------------------------------------- #
# Session creation
# --------------------------------------------------------------------------- #
def start_interview(
    db: Session,
    *,
    role_id: str,
    candidate_name: str,
    resume_text: str,
) -> InterviewSession:
    """Create a session, profile the resume, and generate the first question."""

    # Validates the text (raises InvalidRoleError) and canonicalises it: a
    # preset's id, or the cleaned-up text for a custom role.
    role_id = get_role(role_id).id

    profile = resume_parser.build_profile(resume_text=resume_text, role_id=role_id)

    session = InterviewSession(
        candidate_name=candidate_name or "Candidate",
        role=role_id,
        resume_text=resume_text,
        resume_profile=profile.model_dump(),
        status="in_progress",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    _generate_and_store_question(db, session)
    db.refresh(session)
    return session


# --------------------------------------------------------------------------- #
# Answer submission + advancing the interview
# --------------------------------------------------------------------------- #
def submit_answer(db: Session, *, session_id: str, answer: str) -> InterviewSession:
    """Record an answer and advance the interview (next question or finish)."""

    session = _get_session(db, session_id)
    if session.status == "completed":
        raise InterviewError("This interview is already complete.")

    pending = _pending_question(db, session)
    if pending is None:
        raise InterviewError("There is no open question awaiting an answer.")

    pending.answer = answer.strip()
    pending.answered_at = datetime.now(timezone.utc)
    db.add(pending)
    db.commit()

    answered = _answered_count(db, session)
    if answered >= settings.questions_per_interview:
        _finalise(db, session)
    else:
        _generate_and_store_question(db, session)

    db.refresh(session)
    return session


def _finalise(db: Session, session: InterviewSession) -> None:
    db.refresh(session)
    insights = summary_service.generate_insights(session)
    session.summary = insights.model_dump()
    session.status = "completed"
    session.updated_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()


# --------------------------------------------------------------------------- #
# Question generation (retrieval + generation + persistence)
# --------------------------------------------------------------------------- #
def _generate_and_store_question(db: Session, session: InterviewSession) -> QAPair:
    profile = ResumeProfile(**(session.resume_profile or {}))

    # Retrieve grounded context for this question (resume + role driven).
    context = retrieval.retrieve_context(profile=profile, role_id=session.role)

    existing = _ordered_questions(db, session)
    asked = [qa.question for qa in existing]
    last = existing[-1] if existing else None

    generated = question_generator.generate_question(
        role_id=session.role,
        profile=profile,
        context=context,
        asked_questions=asked,
        last_question=last.question if last else None,
        last_answer=last.answer if last else None,
    )

    # Persist the traceability: which retrieved chunks grounded this question.
    used = generated.context_indices or list(range(min(3, len(context))))
    context_payload = [
        {
            "source": context[i].source,
            "chunk_index": context[i].chunk_index,
            "score": context[i].score,
            "snippet": _snippet(context[i].text),
        }
        for i in used
        if 0 <= i < len(context)
    ]

    qa = QAPair(
        session_id=session.id,
        order_index=len(existing),
        topic=generated.topic,
        difficulty=generated.difficulty,
        rationale=generated.rationale,
        context_chunks=context_payload,
        question=generated.question,
    )
    db.add(qa)
    session.total_questions = len(existing) + 1
    session.updated_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    db.refresh(qa)
    return qa


# --------------------------------------------------------------------------- #
# Helpers / queries
# --------------------------------------------------------------------------- #
def _get_session(db: Session, session_id: str) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if session is None:
        raise InterviewError(f"Interview session '{session_id}' not found.")
    return session


get_session_or_error = _get_session  # public alias for routers


def _ordered_questions(db: Session, session: InterviewSession) -> list[QAPair]:
    return list(
        db.exec(
            select(QAPair)
            .where(QAPair.session_id == session.id)
            .order_by(QAPair.order_index)
        ).all()
    )


def _pending_question(db: Session, session: InterviewSession) -> QAPair | None:
    for qa in _ordered_questions(db, session):
        if qa.answer is None:
            return qa
    return None


def _answered_count(db: Session, session: InterviewSession) -> int:
    return sum(1 for qa in _ordered_questions(db, session) if qa.answer is not None)


def _snippet(text: str, limit: int = 300) -> str:
    s = text.strip().replace("\n", " ")
    return s if len(s) <= limit else s[:limit] + "…"
