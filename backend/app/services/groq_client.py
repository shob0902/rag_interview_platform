"""Thin wrapper around the Groq chat-completions SDK (text generation only).

Groq serves open-weight LLMs (e.g. Llama 3.3) with a fast, generous free tier,
but has **no embeddings API** — embeddings stay on Gemini. This module mirrors
the generation surface of ``gemini_client`` (``generate_text`` / ``generate_json``)
so the two providers are interchangeable behind ``llm.py``.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from groq import Groq

from ..config import get_settings
from .gemini_client import _salvage_json  # reuse the robust JSON recovery

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache
def _client() -> Groq:
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to backend/.env (get a free key at "
            "https://console.groq.com/keys)."
        )
    return Groq(api_key=settings.groq_api_key)


def generate_text(prompt: str, *, temperature: float = 0.4) -> str:
    resp = _client().chat.completions.create(
        model=settings.groq_generation_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


def generate_json(prompt: str, *, temperature: float = 0.4) -> Any:
    """Generate JSON using Groq's OpenAI-compatible JSON mode."""

    resp = _client().chat.completions.create(
        model=settings.groq_generation_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    raw = (resp.choices[0].message.content or "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _salvage_json(raw)
