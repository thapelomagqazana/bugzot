"""Defines the Tag model used for labeling bugs."""

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Tag(Base):
    """User-defined label to categorize bugs (e.g., 'frontend', 'performance', 'regression')."""

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("name", name="uq_tag_name"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), default="#999999")  # Optional hex code for UI badge
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    bugs = relationship("BugTag", back_populates="tag", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """Debug representation for use in logs or admin tooling."""
        return f"<Tag id={self.id} name='{self.name}' color={self.color}>"
