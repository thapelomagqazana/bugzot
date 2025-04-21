from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class BugTag(Base):
    """
    Association table for many-to-many relationship between Bugs and Tags.
    """
    __tablename__ = "bug_tags"

    id = Column(Integer, primary_key=True)
    bug_id = Column(Integer, ForeignKey("bugs.id", ondelete="CASCADE"))
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"))

    # Relationships
    bug = relationship("Bug", back_populates="tags")
    tag = relationship("Tag", back_populates="bugs")
