"""Centralised application configuration.

All runtime configuration is loaded from environment variables (or a local
``.env`` file) so that no secrets or environment-specific values are hard-coded.
See ``.env.example`` for the full list of supported variables.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ``backend/`` directory (two levels up from this file: app/config.py -> app -> backend)
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Strongly-typed application settings sourced from the environment."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM provider selection -------------------------------------------
    # Which provider handles text *generation*. Embeddings always use Gemini
    # (Groq has no embeddings API). "groq" is preferred for its faster, more
    # generous free tier; "gemini" is the fallback.
    llm_provider: str = "groq"

    # --- Google Gemini -----------------------------------------------------
    google_api_key: str = ""
    gemini_generation_model: str = "gemini-flash-lite-latest"
    gemini_embedding_model: str = "models/gemini-embedding-001"

    # --- Groq --------------------------------------------------------------
    groq_api_key: str = ""
    groq_generation_model: str = "openai/gpt-oss-120b"

    # --- Storage paths -----------------------------------------------------
    # SQLite database file used for interview session persistence.
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'data' / 'app.db').as_posix()}"
    # Directory where the persistent Chroma vector store lives.
    chroma_dir: str = str(BACKEND_DIR / "data" / "chroma")
    # Directory scanned by the ingestion script for knowledge-base documents.
    knowledge_base_dir: str = str(BACKEND_DIR / "data" / "knowledge_base")

    # --- RAG tuning --------------------------------------------------------
    chunk_size: int = 2600          # target characters per chunk
    chunk_overlap: int = 300        # overlapping characters between chunks
    retrieval_top_k: int = 6        # chunks returned per retrieval query
    embedding_batch_size: int = 40  # documents embedded per API call
    # Gemini's free embedding tier counts one request per document and caps at
    # 100/min. We throttle below that during bulk ingestion.
    embedding_requests_per_minute: int = 90

    # --- Interview behaviour ----------------------------------------------
    questions_per_interview: int = 5
    max_resume_chars: int = 20000   # guard against pathologically large resumes

    # --- CORS --------------------------------------------------------------
    # Comma-separated list of allowed frontend origins.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (singleton for the process)."""

    return Settings()
