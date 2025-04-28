"""CRUD operations related to the User model."""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional, List
from app.models.users.user import User
from app.schemas.auth import UserRegisterRequest
from datetime import datetime, timezone


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieve a user from the database by their email address.

    Args:
        db (Session): SQLAlchemy database session.
        email (str): Email address to search for.

    Returns:
        User | None: Returns a User instance if found, else None.

    """
    return (
        db.query(User)
        .filter(
            User.email.ilike(email),
        )
        .first()
    )  # Case-insensitive match


def create_user(
    db, payload: UserRegisterRequest, hashed_pw: str, full_name: str | None = None
) -> User:
    """
    Insert new user record with defaults and return it.
    """
    user = User(
        email=payload.email.lower(),
        hashed_password=hashed_pw,
        full_name=full_name,
        role_id=payload.role_id,  # Default to 'reporter' or equivalent
        is_active=payload.active,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role_id or data constraint violation.",
        )
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Retrieve a user by their ID from the database."""
    return (
        db.query(User)
        .filter(User.id == user_id, User.is_active == True, User.is_deleted == False)
        .first()
    )


def increment_login_attempts(db: Session, user: User):
    """Increment login attempts by 1."""
    user.login_attempts += 1
    db.commit()


def reset_login_attempts(db: Session, user: User):
    """Reset the login attempts."""
    user.login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()


def list_users(
    db: Session,
    limit: int,
    offset: int,
    search: Optional[str],
    is_active: Optional[bool],
    sort_by: str,
    sort_dir: str,
) -> (List[User], int):
    """
    Fetch a paginated, filtered, sorted list of users.
    """
    query = db.query(User).filter(User.is_deleted == False)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if sort_by not in {"email", "created_at", "full_name"}:
        sort_by = "created_at"

    sort_column = getattr(User, sort_by)
    sort_column = sort_column.desc() if sort_dir == "desc" else sort_column.asc()

    users = query.order_by(sort_column).offset(offset).limit(limit).all()
    total = query.count()

    return users, total


def update_user_fields(db: Session, user: User, update_data: dict) -> User:
    """
    Update provided fields for a user and commit to DB.
    """
    for field, value in update_data.items():
        setattr(user, field, value)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role_id or data constraint violation.",
        )
    return user


def soft_delete_user(db: Session, target_user_id: int) -> Optional[User]:
    """
    Soft-delete (deactivate) a user by setting is_deleted=True.
    """
    user = (
        db.query(User)
        .filter(User.id == target_user_id, User.is_deleted == False)
        .first()
    )
    if not user:
        return None
    user.is_active = True
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user
