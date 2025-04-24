"""CRUD operations related to the User model."""

from sqlalchemy.orm import Session

from app.models.users.role import DEFAULT_ROLE_ID
from app.models.users.user import User
from app.schemas.auth import UserRegisterRequest


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


def create_user(db: Session, payload: UserRegisterRequest, hashed_pw: str) -> User:
    """Create and persist a new user in the database.

    Args:
        db (Session): SQLAlchemy database session.
        payload (UserRegisterRequest): Pydantic schema with email and
            optional full_name.
        hashed_pw (str): Pre-hashed password to store.

    Returns:
        User: The newly created User instance.

    """
    db_user = User(
        email=payload.email.lower(),  # Normalize email
        hashed_password=hashed_pw,  # Store securely hashed password
        full_name=payload.full_name,  # Optional display name
        role_id=DEFAULT_ROLE_ID,  # Default to 'reporter' or equivalent
    )

    db.add(db_user)  # Stage insert
    db.commit()  # Commit transaction
    db.refresh(db_user)  # Refresh object with DB-generated values

    return db_user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Retrieve a user by their ID from the database."""
    return db.query(User).filter(User.id == user_id, User.is_active == True, User.is_deleted == False).first()
