"""SQLAlchemy model for one-time activation tokens used in account-related workflows."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ActivationKey(Base):
    """Represents a one-time activation token used for user account workflows.

    - Email verification during sign-up
    - Password reset flow (if extended)

    Tokens are tied to users and expire after a set TTL.
    """

    __tablename__ = "activation_keys"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_activation"),
        Index("ix_key_expires", "key", "expires_at"),
        Index("ix_active_keys", "user_id", "is_active"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # FK to user (cascade on user deletion)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Secure, one-time key
    key = Column(String(128), unique=True, nullable=False, index=True)

    # Whether this key is still active (can be used)
    is_active = Column(Boolean, default=True)

    # Timestamp when the key was used
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Expiry timestamp (e.g., 24h from creation)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Audit field: created timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="activation_keys", lazy="joined")

    def __repr__(self) -> str:
        """Debug representation for use in logs or admin tooling."""
        return f"<ActivationKey id={self.id} key='{self.key}' active={self.is_active}>"
