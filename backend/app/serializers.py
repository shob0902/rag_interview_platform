"""Mappers from DB models to API response schemas."""

from __future__ import annotations

from .models import InterviewSession, QAPair
from .roles import get_role
from .schemas import (
    ContextChunk,
    QuestionOut,
    ResumeProfile,
    SessionInsights,
    SessionSummary,
)


def question_to_schema(qa: QAPair) -> QuestionOut:
    return QuestionOut(
        id=qa.id,
        order_index=qa.order_index,
        question=qa.question,
        topic=qa.topic,
        difficulty=qa.difficulty,
        rationale=qa.rationale,
        answer=qa.answer,
        context_chunks=[ContextChunk(**c) for c in (qa.context_chunks or [])],
    )


def profile_to_schema(session: InterviewSession) -> ResumeProfile:
    return ResumeProfile(**(session.resume_profile or {}))


def session_to_summary(session: InterviewSession) -> SessionSummary:
    insights = (
        SessionInsights(**session.summary) if session.summary else None
    )
    return SessionSummary(
        session_id=session.id,
        candidate_name=session.candidate_name,
        role=session.role,
        role_label=get_role(session.role).label,
        status=session.status,
        resume_profile=profile_to_schema(session),
        created_at=session.created_at,
        questions=[question_to_schema(qa) for qa in session.qa_pairs],
        insights=insights,
    )
