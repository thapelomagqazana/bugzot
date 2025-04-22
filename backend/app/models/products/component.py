"""SQLAlchemy model for a product component entity."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Component(Base):
    """Represents a functional sub-module of a Product.

    Helps isolate and categorize bugs for better triaging and ownership.
    """

    __tablename__ = "components"

    id = Column(Integer, primary_key=True)

    # Name must be unique per product
    name = Column(String(100), nullable=False)

    # Optional explanation for context
    description = Column(String(255), nullable=True)

    # Foreign key to owning Product
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    # Logical visibility and deletion flags
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    # Timestamps for audit/history
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="components", lazy="selectin")
    bugs = relationship("Bug", back_populates="component", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("name", "product_id", name="uix_component_per_product"),
        Index("ix_component_product_id", "product_id"),
        Index("ix_component_name", "name"),
    )

    def __repr__(self) -> str:
        """Debug representation for use in logs or admin tooling."""
        return f"<Component id={self.id} name='{self.name}' active={self.is_active}>"
