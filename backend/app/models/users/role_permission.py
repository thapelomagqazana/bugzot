"""SQLAlchemy model for RolePermission join table."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class RolePermission(Base):
    """Join table mapping roles to permissions (many-to-many).

    Includes auditing and soft revocation support.
    """

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    id = Column(Integer, primary_key=True)

    role_id = Column(
        Integer,
        ForeignKey("roles.id", ondelete="CASCADE", name="fk_rolepermission_role"),
        nullable=False,
        index=True,
    )
    permission_id = Column(
        Integer,
        ForeignKey(
            "permissions.id",
            ondelete="CASCADE",
            name="fk_rolepermission_permission",
        ),
        nullable=False,
        index=True,
    )


    # Optional soft revocation
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    role = relationship("Role", back_populates="permissions", lazy="selectin")
    permission = relationship("Permission", back_populates="roles", lazy="selectin")
