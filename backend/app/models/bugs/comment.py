from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Comment(Base):
    """
    Represents a threaded comment or discussion message on a bug.
    Supports visibility, soft deletion, and threading for collaboration.
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)

    # Required comment content
    content = Column(Text, nullable=False)

    # Visibility flag
    is_private = Column(Boolean, default=False)

    # Optional thread support
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)

    # Foreign Keys
    bug_id = Column(Integer, ForeignKey("bugs.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    # Audit + Soft Delete
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bug = relationship("Bug", back_populates="comments", lazy="selectin")
    author = relationship("User", back_populates="comments", lazy="joined")
    parent = relationship("Comment", remote_side=[id], backref="replies", lazy="joined")

    # Indexes
    __table_args__ = (
        Index("ix_comment_bug_id", "bug_id"),
        Index("ix_comment_author_id", "author_id"),
        Index("ix_comment_visibility", "is_private"),
    )

    def __repr__(self):
        """
        Debug representation for use in logs or admin tooling.
        """
        return f"<Comment id={self.id} name='{self.content}' private={self.is_private}>"
