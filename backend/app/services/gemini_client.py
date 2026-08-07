"""Thin wrapper around the Google Gemini SDK.

Centralising all Gemini access here means the rest of the codebase depends on a
small, well-defined surface (``embed_documents``, ``embed_query``,
``generate_json``, ``generate_text``) rather than the SDK directly. Swapping the
provider later only touches this file.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import google.generativeai as genai

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_configured = False


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your "
            "free Google AI Studio API key."
        )
    genai.configure(api_key=settings.google_api_key)
    _configured = True


# --------------------------------------------------------------------------- #
# Embeddings
# --------------------------------------------------------------------------- #
def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of documents for storage in the vector DB."""

    _ensure_configured()
    if not texts:
        return []
    result = genai.embed_content(
        model=settings.gemini_embedding_model,
        content=texts,
        task_type="retrieval_document",
    )
    return result["embedding"]


def embed_query(text: str) -> list[float]:
    """Embed a single query string for retrieval."""

    _ensure_configured()
    result = genai.embed_content(
        model=settings.gemini_embedding_model,
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
def generate_text(prompt: str, *, temperature: float = 0.4) -> str:
    """Generate free-form text."""

    _ensure_configured()
    model = genai.GenerativeModel(settings.gemini_generation_model)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": temperature},
    )
    return (response.text or "").strip()


def generate_json(prompt: str, *, temperature: float = 0.4) -> Any:
    """Generate a response constrained to valid JSON and parse it.

    Uses Gemini's ``response_mime_type=application/json`` so the model returns
    machine-readable output. Falls back to best-effort extraction if needed.
    """

    _ensure_configured()
    model = genai.GenerativeModel(settings.gemini_generation_model)
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
    )
    raw = (response.text or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _salvage_json(raw)


def _salvage_json(raw: str) -> Any:
    """Best-effort recovery when the model wraps JSON in prose or code fences."""

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        # Drop a leading language hint like "json\n".
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1]
    start = min(
        (i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1),
        default=-1,
    )
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            pass
    logger.error("Failed to parse JSON from model output: %s", raw[:500])
    raise ValueError("Model did not return valid JSON.")
