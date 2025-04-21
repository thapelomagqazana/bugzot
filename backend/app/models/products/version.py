from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class Version(Base):
    """
    Represents a version or release of a product.
    Each bug can optionally be associated with a version.
    """
    __tablename__ = "versions"
    __table_args__ = (
        UniqueConstraint("name", "product_id", name="uix_version_per_product"),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)  # e.g. v1.2.0, 2024.03, etc.
    description = Column(String(255), nullable=True)

    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    release_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="versions")
    bugs = relationship("Bug", back_populates="version", lazy="selectin")

    def __repr__(self):
        """
        Debug representation for use in logs or admin tooling.
        """
        return f"<Version id={self.id} name='{self.name}' active={self.is_active}>"
