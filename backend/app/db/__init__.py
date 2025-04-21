"""
Database connection setup for SQLAlchemy with PostgreSQL.
Provides session and engine objects to be reused throughout the app.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import get_settings

# Load settings
settings = get_settings()

# SQLAlchemy engine (sync) — works with Alembic too
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
