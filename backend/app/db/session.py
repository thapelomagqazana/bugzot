"""Session management and FastAPI dependency injection for database access."""

from collections.abc import Generator

from app.db import SessionLocal


def get_db() -> Generator:
    """Return a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
