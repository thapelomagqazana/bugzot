"""Database connection setup for SQLAlchemy with PostgreSQL.

Provides session and engine objects to be reused throughout the app.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import get_settings

# Load application settings (uses Pydantic-based config)
settings = get_settings()

# Create SQLAlchemy engine for PostgreSQL (sync)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,     # Helps avoid stale DB connections
    pool_size=10,           # Recommended baseline for production
    max_overflow=20,        # Burst capacity
    future=True,             # Ensures 2.0-style behavior
)

# Reusable session factory for dependency injection and CRUD
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# --- Optional Testing Setup (for pytest) ---
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://test_user:test_pass@localhost:5434/test_db")

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,     # Helps avoid stale DB connections
    pool_size=10,           # Recommended baseline for production
    max_overflow=20,        # Burst capacity
    future=True,             # Ensures 2.0-style behavior
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)
