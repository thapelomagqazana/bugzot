"""Base class for SQLAlchemy models.

All models should inherit from this for consistent metadata management.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Global declarative base class for SQLAlchemy models.

    Used by all models for shared metadata and base functionality.
    """
