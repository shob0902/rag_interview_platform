"""Database models for interview persistence.

The schema captures the full traceability chain required by the assignment:

    Context (retrieved chunks) -> Question -> Answer -> Storage

An ``InterviewSession`` owns an ordered list of ``QAPair`` rows. Each ``QAPair``
stores not only the question and answer text but also *how* the question was
produced (the retrieved context chunks, topic, difficulty and rationale) so the
generation of every question is auditable after the fact.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Column, Field, JSON, Relationship, SQLModel

# NOTE: intentionally NOT using ``from __future__ import annotations`` here.
# SQLModel/SQLAlchemy must be able to *evaluate* the Relationship annotations at
# class-definition time; postponed (string) annotations break relationship
# resolution ("generic class as the argument to relationship()").


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InterviewSession(SQLModel, table=True):
    """A single candidate interview session."""

    __tablename__ = "interview_sessions"

    id: str = Field(default_factory=_uuid, primary_key=True)
    candidate_name: str = Field(default="Candidate")
    role: str = Field(index=True)

    # Full parsed resume text plus structured extraction (skills, technologies…).
    resume_text: str = Field(default="")
    resume_profile: dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Lifecycle: "in_progress" | "completed".
    status: str = Field(default="in_progress", index=True)
    total_questions: int = Field(default=0)

    # Final structured summary/insights (populated when the interview ends).
    summary: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    qa_pairs: List["QAPair"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={
            "order_by": "QAPair.order_index",
            "cascade": "all, delete-orphan",
        },
    )


class QAPair(SQLModel, table=True):
    """One question/answer turn within a session, with full generation trace."""

    __tablename__ = "qa_pairs"

    id: str = Field(default_factory=_uuid, primary_key=True)
    session_id: str = Field(foreign_key="interview_sessions.id", index=True)
    order_index: int = Field(default=0)

    # --- Generation trace (the "Context -> Question" half of the pipeline) --
    topic: str = Field(default="")
    difficulty: str = Field(default="medium")
    rationale: str = Field(default="")
    # Retrieved chunks that grounded this question (source, snippet, score…).
    context_chunks: list = Field(default_factory=list, sa_column=Column(JSON))

    question: str = Field(default="")

    # --- Candidate response (the "Answer -> Storage" half) -----------------
    answer: Optional[str] = Field(default=None)
    answered_at: Optional[datetime] = Field(default=None)

    created_at: datetime = Field(default_factory=_now)

    session: Optional[InterviewSession] = Relationship(back_populates="qa_pairs")
