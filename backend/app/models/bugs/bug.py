"""Defines the Bug model and supporting enums for bug tracking, including priority and status."""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class BugStatus(str, enum.Enum):
    """Enumeration for possible bug statuses."""

    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    FIXED = "FIXED"
    VERIFIED = "VERIFIED"
    CLOSED = "CLOSED"


class BugPriority(str, enum.Enum):
    """Enumeration for bug priority levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Bug(Base):
    """Main model for tracking bugs in BugZot.

    Includes priority, status, soft deletion, and relationships to users,
    products, and components.
    """

    __tablename__ = "bugs"

    id = Column(Integer, primary_key=True)

    # Metadata
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(BugStatus), default=BugStatus.NEW, nullable=False)
    priority = Column(Enum(BugPriority), default=BugPriority.MEDIUM, nullable=False)

    # Soft delete
    is_deleted = Column(Boolean, default=False)

    # Foreign keys
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    component_id = Column(Integer, ForeignKey("components.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    reporter = relationship("User", back_populates="reported_bugs", foreign_keys=[reporter_id], lazy="joined")
    assignee = relationship("User", back_populates="assigned_bugs", foreign_keys=[assignee_id], lazy="joined")
    product = relationship("Product", back_populates="bugs", lazy="joined")
    component = relationship("Component", back_populates="bugs", lazy="joined")
    comments = relationship("Comment", back_populates="bug", cascade="all, delete-orphan", lazy="selectin")
    attachments = relationship("Attachment", back_populates="bug", cascade="all, delete-orphan", lazy="selectin")
    tags = relationship("BugTag", back_populates="bug", cascade="all, delete-orphan", lazy="selectin")
    # New FK in Bug
    version_id = Column(Integer, ForeignKey("versions.id", ondelete="SET NULL"), nullable=True)
    version = relationship("Version", back_populates="bugs")


    # Indexes for fast querying
    __table_args__ = (
        Index("ix_bug_status", "status"),
        Index("ix_bug_product_component", "product_id", "component_id"),
        Index("ix_bug_assignee", "assignee_id"),
        Index("ix_bug_priority", "priority"),
    )

    def __repr__(self) -> str:
        """Debug representation for use in logs or admin tooling."""
        return f"<Bug id={self.id} title='{self.title}' status={self.status}>"
