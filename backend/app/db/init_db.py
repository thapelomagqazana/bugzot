from app.models.users.role import Role
from sqlalchemy.orm import Session

def seed_roles(db: Session):
    if not db.query(Role).filter_by(id=1).first():
        db.add_all([
            Role(id=1, name="reporter", description="Default user role", is_system=True),
            Role(id=2, name="developer", description="Developer role", is_system=True),
            Role(id=3, name="admin", description="Admin role", is_system=True),
        ])
