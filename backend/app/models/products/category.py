"""SQLAlchemy model for product categories used for organizing products."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Category(Base):
    """Represents a product grouping or classification.

    Used to organize large collections of products into logical groups
    (e.g., "Dev Tools", "Mobile Apps") for filtering, reporting, and admin
    operations. Supports soft deletion, visibility toggles, and audit trails.
    """

    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_category_name", "name"),  # Fast lookup by name
        Index("ix_category_active_name", "is_active", "name"),
    )

    id = Column(Integer, primary_key=True)

    # Display name of the category (e.g., "Dev Tools")
    name = Column(String(100), nullable=False, unique=True)

    # Optional slug for SEO-friendly or programmatic routes (e.g., "dev-tools")
    slug = Column(String(120), unique=True, nullable=True)

    # Brief description to explain the category purpose in admin UI or documentation
    description = Column(String(255), nullable=True)

    # Whether this category is visible to users/admins or deprecated
    is_active = Column(Boolean, default=True)

    # Soft deletion flag (hides the category without removing from DB)
    is_deleted = Column(Boolean, default=False)

    # Timestamps for creation and last update
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Optional auditing fields: which user created or updated this category
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationship to products that belong to this category
    products = relationship(
        "Product",
        back_populates="category",
        lazy="selectin",  # Efficient loading for frontend grids/lists
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Debug representation for use in logs or admin tooling."""
        return f"<Category id={self.id} name='{self.name}' active={self.is_active}>"
