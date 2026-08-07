"""LLM generation dispatcher.

Provides a single generation surface (``generate_text`` / ``generate_json``) that
routes to the configured provider (``LLM_PROVIDER``: "groq" or "gemini"). This
keeps every caller (resume profiling, question generation, summary) decoupled
from the concrete provider, so switching is a one-line config change.

Embeddings are intentionally NOT dispatched here — they always use Gemini via
``gemini_client`` because Groq has no embeddings API.
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import get_settings
from . import gemini_client, groq_client

logger = logging.getLogger(__name__)
settings = get_settings()


def _provider():
    return groq_client if settings.llm_provider.lower() == "groq" else gemini_client


def generate_text(prompt: str, *, temperature: float = 0.4) -> str:
    return _provider().generate_text(prompt, temperature=temperature)


def generate_json(prompt: str, *, temperature: float = 0.4) -> Any:
    return _provider().generate_json(prompt, temperature=temperature)
