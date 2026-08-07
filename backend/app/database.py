"""Database engine and session management.

Uses SQLite by default (zero external dependencies for the reviewer) but the
connection string is fully configurable via ``DATABASE_URL`` so the same code
runs against PostgreSQL in a real deployment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()

# ``check_same_thread`` is required so the SQLite connection can be shared across
# FastAPI's threadpool workers.
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, echo=False, connect_args=_connect_args)


def init_db() -> None:
    """Create tables and ensure the SQLite parent directory exists."""

    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Import models so they are registered on SQLModel.metadata before create_all.
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a database session per request."""

    with Session(engine) as session:
        yield session
