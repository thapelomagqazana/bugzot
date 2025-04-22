"""Seed initial roles into the database if they do not exist."""

from sqlalchemy.orm import Session

from app.models.users import Role


def seed_roles(db: Session) -> None:
    """Insert default system roles if not already present."""
    if not db.query(Role).filter_by(id=1).first():
        db.add_all([
            Role(id=1, name="reporter", description="Default user role", is_system=True),
            Role(id=2, name="developer", description="Developer role", is_system=True),
            Role(id=3, name="admin", description="Admin role", is_system=True),
        ])

