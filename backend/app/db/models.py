"""
SQLAlchemy ORM models.
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base

# Base class for all models
Base = declarative_base()

class User(Base):
    """
    User model representing registered users.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
