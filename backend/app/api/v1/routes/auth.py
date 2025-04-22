from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import UserRegisterRequest, UserResponse
from app.crud.user import create_user, get_user_by_email
from app.core.security import hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    - Checks for duplicate email (case-insensitive).
    - Hashes password using bcrypt.
    - Assigns default role (e.g., reporter).
    - Returns sanitized user data (no password).

    Args:
        payload (UserRegisterRequest): Email, password, and optional full name.
        db (Session): SQLAlchemy DB session (injected).

    Returns:
        UserResponse: User info (id, email, full_name, role_id, created_at).
    """
    existing_user = get_user_by_email(db, email=payload.email.lower())
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered."
        )

    user = create_user(db, payload, hashed_pw=hash_password(payload.password))
    return user
