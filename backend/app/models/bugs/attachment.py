"""Defines the Attachment model for storing bug-related files."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Attachment(Base):
    """Stores metadata for bug-related attachments.

    Supports versioning, soft deletion, and uploader tracking.
    """

    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)

    # File metadata
    filename = Column(String, nullable=False, index=True)
    file_path = Column(String, nullable=False)  # S3 path, local path, etc.
    mime_type = Column(String, nullable=True)  # For previews / validation
    file_size = Column(Integer, nullable=True)  # In bytes

    # Versioning
    version = Column(Integer, default=1, nullable=False)
    is_latest = Column(Boolean, default=True, nullable=False)

    # Timestamps and audit
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    bug_id = Column(Integer, ForeignKey("bugs.id", ondelete="CASCADE"), nullable=False)
    uploaded_by_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    bug = relationship("Bug", back_populates="attachments")
    uploaded_by = relationship("User", lazy="joined")

    __table_args__ = (Index("ix_attachment_bug_version", "bug_id", "version"),)

    def __repr__(self) -> str:
        """Debug representation for use in logs or admin tooling."""
        return f"<Attachment id={self.id} filename='{self.filename}' file_path={self.file_path}>"
