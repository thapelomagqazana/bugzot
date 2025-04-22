"""SQLAlchemy model for the Role entity."""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

DEFAULT_ROLE_ID = 1

class Role(Base):
    """Represents a user role such as 'admin', 'developer', 'reporter'.

    Supports soft deletion, auditing, and permission mapping.
    """

    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("name", name="uq_role_name"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Role name (must be unique)
    name = Column(String(50), nullable=False, index=True)

    # Optional description
    description = Column(String(255), nullable=True)

    # System-level control (reserved roles)
    is_system = Column(Boolean, default=False)

    # Soft delete & auditing
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="role", lazy="selectin")
    permissions = relationship(
        "RolePermission",
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return debug string representation for Role."""
        return f"<Role id={self.id} name='{self.name}' active={self.is_active}>"
