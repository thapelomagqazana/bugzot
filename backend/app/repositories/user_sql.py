from sqlalchemy.orm import Session
from app.db.models import User
from app.repositories.base import BaseRepository
from app.utils.security import hash_password
from typing import List, Optional

class UserSQLRepository(BaseRepository[User]):
    """
    User repository for SQL-based databases (PostgreSQL, MySQL).
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, obj_data: dict) -> User:
        new_user = User(
            name=obj_data["name"].strip(),
            email=obj_data["email"].strip().lower(),
            hashed_password=hash_password(obj_data["password"]),
            role=obj_data.get("role", "user")
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def update(self, id: int, obj_data: dict) -> Optional[User]:
        user = self.get_by_id(id)
        if not user:
            return None
        
        for key, value in obj_data.items():
            if value is not None:
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, id: int) -> bool:
        user = self.get_by_id(id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True
