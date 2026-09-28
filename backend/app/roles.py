"""Role registry.

Each preset role maps to a human-readable label, a short description used to
steer question generation, and the vector-store *collection* that holds its
role-specific knowledge base. Adding a new role is a matter of adding one entry
here plus ingesting documents tagged with its ``id`` (see ``scripts/ingest.py``).

Candidates may also type any other role. ``get_role`` turns that free text into
an ad-hoc ``Role`` (``custom=True``); whether an existing knowledge base applies
to it is decided in ``services/retrieval.py``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    id: str
    label: str
    description: str
    # Books that make up this role's knowledge base (informational; ingestion
    # simply reads whatever files are placed in the role's KB sub-directory).
    recommended_sources: tuple[str, ...] = ()
    # True for a role the candidate typed in rather than one of ROLES.
    custom: bool = False


class InvalidRoleError(ValueError):
    """The submitted role text is empty or too long."""


MAX_ROLE_CHARS = 60


ROLES: dict[str, Role] = {
    "ai_ml_engineer": Role(
        id="ai_ml_engineer",
        label="AI / ML Engineer",
        description=(
            "Machine learning fundamentals, model training and evaluation, "
            "supervised/unsupervised learning, bias-variance, generalization, "
            "and applied ML system design."
        ),
        recommended_sources=("Machine Learning — Tom Mitchell",),
    ),
    "data_scientist": Role(
        id="data_scientist",
        label="Data Scientist",
        description=(
            "Applied machine learning with Python, feature engineering, model "
            "selection, statistical reasoning and practical algorithm intuition."
        ),
        recommended_sources=(
            "Introduction to Machine Learning with Python",
            "Master Machine Learning Algorithms — Jason Brownlee",
        ),
    ),
    "backend_engineer": Role(
        id="backend_engineer",
        label="Backend Engineer",
        description=(
            "API and service design, data modelling, system architecture, "
            "scalability, error handling and separation of concerns."
        ),
        recommended_sources=(),
    ),
}

DEFAULT_ROLE = "ai_ml_engineer"


def get_role(role_id: str) -> Role:
    """Resolve a preset role by id or label, or build a custom role.

    Free text that doesn't match a preset becomes a custom role whose id and
    label are the cleaned-up text, so it round-trips through the session's
    ``role`` column unchanged.
    """

    # Collapse whitespace and drop control characters: the text is interpolated
    # into LLM prompts, so keep it to a single short line.
    raw = str(role_id or "")
    text = " ".join("".join(ch if ch.isprintable() else " " for ch in raw).split())
    if not text:
        raise InvalidRoleError("Please enter a target role.")
    if len(text) > MAX_ROLE_CHARS:
        raise InvalidRoleError(
            f"Role must be at most {MAX_ROLE_CHARS} characters."
        )

    key = text.lower()
    for role in ROLES.values():
        if key in (role.id, role.label.lower()):
            return role

    return Role(
        id=text,
        label=text,
        description=(
            f"The core concepts, skills and responsibilities expected of a {text}."
        ),
        custom=True,
    )


def list_roles() -> list[Role]:
    return list(ROLES.values())
