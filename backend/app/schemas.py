"""Pydantic request/response schemas (the API contract).

These are intentionally separate from the SQLModel table classes so the wire
format is decoupled from the storage format.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Roles
# --------------------------------------------------------------------------- #
class RoleInfo(BaseModel):
    id: str
    label: str
    description: str
    document_count: int = 0


# --------------------------------------------------------------------------- #
# Resume profile (structured extraction)
# --------------------------------------------------------------------------- #
class ResumeProfile(BaseModel):
    skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    experience_summary: str = ""
    seniority: str = "unknown"


# --------------------------------------------------------------------------- #
# Context / retrieval trace
# --------------------------------------------------------------------------- #
class ContextChunk(BaseModel):
    source: str
    chunk_index: int
    score: float
    snippet: str


# --------------------------------------------------------------------------- #
# Questions
# --------------------------------------------------------------------------- #
class QuestionOut(BaseModel):
    id: str
    order_index: int
    question: str
    topic: str
    difficulty: str
    rationale: str
    answer: Optional[str] = None
    context_chunks: list[ContextChunk] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Session lifecycle
# --------------------------------------------------------------------------- #
class StartInterviewResponse(BaseModel):
    session_id: str
    role: str
    role_label: str
    candidate_name: str
    resume_profile: ResumeProfile
    total_questions: int
    question: QuestionOut


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(min_length=1)


class SubmitAnswerResponse(BaseModel):
    session_id: str
    status: str  # "in_progress" | "completed"
    next_question: Optional[QuestionOut] = None
    questions_answered: int
    total_questions: int


class SessionInsights(BaseModel):
    overall_assessment: str = ""
    strengths: list[str] = Field(default_factory=list)
    areas_to_improve: list[str] = Field(default_factory=list)
    recommendation: str = ""
    score: Optional[int] = None  # 0-100


class SessionSummary(BaseModel):
    session_id: str
    candidate_name: str
    role: str
    role_label: str
    status: str
    resume_profile: ResumeProfile
    created_at: datetime
    questions: list[QuestionOut]
    insights: Optional[SessionInsights] = None
