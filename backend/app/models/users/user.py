"""User model definition and relationships."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.users.role import DEFAULT_ROLE_ID


class User(Base):
    """User model storing credentials, roles, metadata, and behavioral tracking.

    Enhancements:
    - last_login and login_attempts for security/throttling
    - full_name fallback handling (to be used in app logic)
    - sensible default for role_id (enforced at DB/app level)
    - partial unique constraint: (email, is_deleted=False)
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    # Optional display name
    full_name = Column(String, nullable=True)

    # Role relationship
    role_id = Column(
        Integer,
        ForeignKey("roles.id"),
        nullable=False,
        default=DEFAULT_ROLE_ID,
    )  # Default to 'reporter' role

    role = relationship("Role", back_populates="users")

    # State flags
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Tracking timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Security auditing
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_attempts = Column(Integer, default=0)

    # Relationships
    reported_bugs = relationship(
        "Bug",
        back_populates="reporter",
        foreign_keys="Bug.reporter_id",
        lazy="selectin",
    )
    assigned_bugs = relationship(
        "Bug",
        back_populates="assignee",
        foreign_keys="Bug.assignee_id",
        lazy="selectin",
    )

    comments = relationship("Comment", back_populates="author", lazy="selectin")
    activation_keys = relationship(
        "ActivationKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Unique constraint workaround for soft delete
    __table_args__ = (
        Index(
            "uq_users_email_active", "email", postgresql_where=~is_deleted, unique=True
        ),
    )

    def __repr__(self) -> str:
        """Return debug representation for logs/admin tools."""
        return f"<User id={self.id} name='{self.full_name}' active={self.is_active}>"
