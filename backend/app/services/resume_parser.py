"""Resume ingestion and structured extraction.

Two stages:

1. **Text extraction** — accept a PDF or plain-text upload and return clean
   UTF-8 text (``extract_text``).
2. **Structured profiling** — use the LLM to turn free-form resume text into a
   structured :class:`ResumeProfile` (skills, technologies, domains, seniority).
   A deterministic keyword fallback keeps the system usable if the LLM call
   fails, so resume parsing never becomes a hard dependency on the model.
"""

from __future__ import annotations

import io
import logging
import re

from pypdf import PdfReader

from ..config import get_settings
from ..roles import get_role
from ..schemas import ResumeProfile
from . import llm

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_text(*, data: bytes, filename: str) -> str:
    """Extract text from an uploaded resume (PDF or text)."""

    name = (filename or "").lower()
    if name.endswith(".pdf"):
        text = _extract_pdf(data)
    else:
        text = data.decode("utf-8", errors="ignore")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ValueError("Could not extract any text from the uploaded resume.")
    return text[: settings.max_resume_chars]


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover - malformed PDF page
            logger.warning("Failed to extract a PDF page: %s", exc)
    return "\n".join(parts)


_PROFILE_PROMPT = """You are an expert technical recruiter analysing a resume for the role of \
"{role_label}" ({role_description}).

Extract a structured profile from the resume text below. Focus on what is \
relevant to evaluating this candidate for the role.

Return JSON with exactly these keys:
- "skills": array of concrete skills/competencies (max 12)
- "technologies": array of tools, languages, frameworks, libraries (max 12)
- "domains": array of problem domains / areas of exposure (e.g. "NLP", "computer vision", "distributed systems") (max 8)
- "experience_summary": 2-3 sentence plain-language summary of the candidate's background
- "seniority": one of "junior", "mid", "senior", or "unknown"

Resume text:
\"\"\"
{resume_text}
\"\"\"
"""


def build_profile(*, resume_text: str, role_id: str) -> ResumeProfile:
    """Produce a structured resume profile, with a keyword fallback."""

    role = get_role(role_id)
    prompt = _PROFILE_PROMPT.format(
        role_label=role.label,
        role_description=role.description,
        resume_text=resume_text[:8000],
    )
    try:
        data = llm.generate_json(prompt, temperature=0.2)
        return ResumeProfile(
            skills=_as_str_list(data.get("skills"))[:12],
            technologies=_as_str_list(data.get("technologies"))[:12],
            domains=_as_str_list(data.get("domains"))[:8],
            experience_summary=str(data.get("experience_summary", "")).strip(),
            seniority=_norm_seniority(data.get("seniority")),
        )
    except Exception as exc:
        logger.warning("LLM resume profiling failed, using fallback: %s", exc)
        return _fallback_profile(resume_text)


def _as_str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    out, seen = [], set()
    for item in value:
        s = str(item).strip()
        key = s.lower()
        if s and key not in seen:
            seen.add(key)
            out.append(s)
    return out


def _norm_seniority(value) -> str:
    v = str(value or "").lower()
    return v if v in {"junior", "mid", "senior"} else "unknown"


# Minimal keyword bank for the deterministic fallback path.
_TECH_KEYWORDS = [
    "python", "java", "c++", "javascript", "typescript", "go", "rust", "sql",
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "pandas",
    "numpy", "fastapi", "flask", "django", "react", "node", "docker",
    "kubernetes", "aws", "gcp", "azure", "spark", "hadoop", "kafka",
    "postgres", "mongodb", "redis", "transformers", "huggingface", "langchain",
]
_DOMAIN_KEYWORDS = [
    "nlp", "computer vision", "reinforcement learning", "recommendation",
    "time series", "deep learning", "machine learning", "data engineering",
    "mlops", "distributed systems", "microservices",
]


def _fallback_profile(resume_text: str) -> ResumeProfile:
    lowered = resume_text.lower()
    techs = [t for t in _TECH_KEYWORDS if t in lowered]
    domains = [d for d in _DOMAIN_KEYWORDS if d in lowered]
    return ResumeProfile(
        skills=techs[:12],
        technologies=techs[:12],
        domains=domains[:8],
        experience_summary=resume_text[:300].replace("\n", " ").strip(),
        seniority="unknown",
    )
