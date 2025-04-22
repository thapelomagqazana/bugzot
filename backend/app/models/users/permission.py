"""Defines the Permission model representing system-level access rights."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Permission(Base):
    """Represents an individual system-level permission (e.g., 'create_bug').

    Permissions are assigned to roles through RolePermission mappings.
    """

    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("name", name="uq_permission_name"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Permission identifier (e.g., 'edit_bug', 'delete_user')
    name = Column(String(100), nullable=False)

    # Optional display text or use-case explanation
    description = Column(String(255), nullable=True)

    # Permission activation toggle (can be soft-disabled)
    is_active = Column(Boolean, default=True)

    # Auditing fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Many-to-many backref (via RolePermission)
    roles = relationship("RolePermission", back_populates="permission", lazy="selectin")

    def __repr__(self) -> str:
        """Debug representation for use in logs or admin tooling."""
        return f"<Permission id={self.id} name='{self.name}' active={self.is_active}>"
