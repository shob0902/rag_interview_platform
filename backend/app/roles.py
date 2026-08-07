"""Role registry.

Each role maps to a human-readable label, a short description used to steer
question generation, and the vector-store *collection* that holds its
role-specific knowledge base. Adding a new role is a matter of adding one entry
here plus ingesting documents tagged with its ``id`` (see ``scripts/ingest.py``).
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
    role = ROLES.get(role_id)
    if role is None:
        raise KeyError(f"Unknown role '{role_id}'. Known roles: {list(ROLES)}")
    return role


def list_roles() -> list[Role]:
    return list(ROLES.values())
