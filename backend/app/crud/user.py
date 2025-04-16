"""
CRUD operations for the User model.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password


def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user in the database.
    """
    hashed_password = hash_password(user.password)
    db_user = User(
        name=user.name.strip(),
        email=user.email.strip().lower(),
        hashed_password=hashed_password,
        role=user.role.strip().lower() if user.role else "user"  # Handle role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int) -> Optional[User]:
    """
    Retrieve a user by their ID.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by their email.
    """
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Retrieve all users with pagination.
    """
    return db.query(User).offset(skip).limit(limit).all()


def update_user(db: Session, db_user: User, updates: UserUpdate) -> User:
    """
    Update an existing user's details.
    """
    if updates.name:
        db_user.name = updates.name.strip()
    if updates.email:
        db_user.email = updates.email.strip().lower()
    if updates.password:
        db_user.hashed_password = hash_password(updates.password)
    if updates.role:
        db_user.role = updates.role.strip().lower()

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, db_user: User) -> None:
    """
    Delete a user from the database.
    """
    db.delete(db_user)
    db.commit()
