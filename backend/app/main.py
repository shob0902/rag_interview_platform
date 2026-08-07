"""FastAPI application entrypoint.

Wires together configuration, database initialisation, CORS for the React
frontend, and the interview router. Run locally with:

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import interview

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# Chroma's telemetry emitter is buggy and noisy; we disable telemetry in the
# client settings but also silence its logger to keep output clean.
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

settings = get_settings()

app = FastAPI(
    title="AI Role-Based Candidate Screening",
    description=(
        "RAG-powered technical interview system. Dynamically generates "
        "interview questions grounded in a role-specific knowledge base, "
        "tailored to the candidate's resume."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview.router)


@app.on_event("startup")
def _on_startup() -> None:
    init_db()
    logging.getLogger(__name__).info("Database initialised.")


@app.get("/api/health", tags=["health"])
def health() -> dict:
    generation_model = (
        settings.groq_generation_model
        if settings.llm_provider.lower() == "groq"
        else settings.gemini_generation_model
    )
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "generation_model": generation_model,
        "embedding_model": settings.gemini_embedding_model,
        "gemini_configured": bool(settings.google_api_key),
        "groq_configured": bool(settings.groq_api_key),
    }
