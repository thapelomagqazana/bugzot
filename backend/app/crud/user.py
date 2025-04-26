"""CRUD operations related to the User model."""

from sqlalchemy.orm import Session

from app.models.users.user import User
from app.schemas.auth import UserRegisterRequest
from datetime import datetime


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
    db.commit()
    db.refresh(user)
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
