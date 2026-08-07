"""HTTP API for the interview lifecycle.

Endpoints map onto the interview lifecycle stages; each one validates its input
and delegates to the service layer, keeping the transport concerns (parsing
multipart uploads, status codes) separate from business logic.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from ..config import get_settings
from ..database import get_session
from ..roles import list_roles
from ..schemas import (
    RoleInfo,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SessionSummary,
)
from ..serializers import (
    profile_to_schema,
    question_to_schema,
    session_to_summary,
)
from ..services import interview_service, resume_parser, vector_store

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api", tags=["interview"])


# --------------------------------------------------------------------------- #
# Roles
# --------------------------------------------------------------------------- #
@router.get("/roles", response_model=list[RoleInfo])
def get_roles() -> list[RoleInfo]:
    return [
        RoleInfo(
            id=role.id,
            label=role.label,
            description=role.description,
            document_count=vector_store.count(role.id),
        )
        for role in list_roles()
    ]


# --------------------------------------------------------------------------- #
# Start interview
# --------------------------------------------------------------------------- #
@router.post("/interviews/start", response_model=StartInterviewResponse)
async def start_interview(
    role: str = Form(...),
    candidate_name: str = Form("Candidate"),
    resume_text: str | None = Form(None),
    resume_file: UploadFile | None = File(None),
    db: Session = Depends(get_session),
) -> StartInterviewResponse:
    # Resolve resume text from either an uploaded file or a pasted string.
    if resume_file is not None:
        data = await resume_file.read()
        try:
            text = resume_parser.extract_text(
                data=data, filename=resume_file.filename or "resume"
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    elif resume_text and resume_text.strip():
        text = resume_text.strip()[: settings.max_resume_chars]
    else:
        raise HTTPException(
            status_code=422,
            detail="Provide a resume: either upload a file or paste resume text.",
        )

    try:
        session = interview_service.start_interview(
            db, role_id=role, candidate_name=candidate_name, resume_text=text
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to start interview")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to start interview: {exc}",
        ) from exc

    first_question = session.qa_pairs[0]
    return StartInterviewResponse(
        session_id=session.id,
        role=session.role,
        candidate_name=session.candidate_name,
        resume_profile=profile_to_schema(session),
        total_questions=settings.questions_per_interview,
        question=question_to_schema(first_question),
    )


# --------------------------------------------------------------------------- #
# Submit answer
# --------------------------------------------------------------------------- #
@router.post(
    "/interviews/{session_id}/answer", response_model=SubmitAnswerResponse
)
def submit_answer(
    session_id: str,
    payload: SubmitAnswerRequest,
    db: Session = Depends(get_session),
) -> SubmitAnswerResponse:
    try:
        session = interview_service.submit_answer(
            db, session_id=session_id, answer=payload.answer
        )
    except interview_service.InterviewError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to submit answer")
        raise HTTPException(
            status_code=502, detail=f"Failed to process answer: {exc}"
        ) from exc

    answered = sum(1 for qa in session.qa_pairs if qa.answer is not None)
    next_q = None
    if session.status != "completed":
        pending = [qa for qa in session.qa_pairs if qa.answer is None]
        if pending:
            next_q = question_to_schema(pending[-1])

    return SubmitAnswerResponse(
        session_id=session.id,
        status=session.status,
        next_question=next_q,
        questions_answered=answered,
        total_questions=settings.questions_per_interview,
    )


# --------------------------------------------------------------------------- #
# Fetch full session (transcript + insights)
# --------------------------------------------------------------------------- #
@router.get("/interviews/{session_id}", response_model=SessionSummary)
def get_session_summary(
    session_id: str,
    db: Session = Depends(get_session),
) -> SessionSummary:
    try:
        session = interview_service.get_session_or_error(db, session_id)
    except interview_service.InterviewError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return session_to_summary(session)
