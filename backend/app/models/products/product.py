"""SQLAlchemy model for a product entity."""

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


class Product(Base):
    """Represents a top-level software product managed by the organization.

    Supports soft deletion, visibility, and metadata tracking.
    """

    __tablename__ = "products"
    __table_args__ = (
        Index("ix_product_name", "name"),  # Support fast lookup by name
    )

    id = Column(Integer, primary_key=True)

    # Human-readable, unique name
    name = Column(String(100), unique=True, nullable=False)

    # Optional description for context
    description = Column(String(255), nullable=True)

    # Visibility control (e.g., for internal tools or legacy products)
    is_active = Column(Boolean, default=True)

    # Soft deletion
    is_deleted = Column(Boolean, default=False)

    # Foreign Key to category
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    category = relationship("Category", back_populates="products", lazy="joined")

    # Auditing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    components = relationship("Component", back_populates="product", cascade="all, delete-orphan", lazy="selectin")
    bugs = relationship("Bug", back_populates="product", cascade="all, delete-orphan", lazy="selectin")
    versions = relationship("Version", back_populates="product", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        """Debug representation for use in logs or admin tooling."""
        return f"<Product id={self.id} name='{self.name}' active={self.is_active}>"
