"""Routes for managing auth-related operations."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import TOKEN_TYPE_BEARER
from app.core.security import create_access_token, hash_password, verify_password
from app.crud.user import create_user, get_user_by_email
from app.db.session import get_db

if TYPE_CHECKING:
    from app.models.users.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED,
)
def register_user(payload: UserRegisterRequest, db: Annotated[Session, Depends(get_db)]) -> UserResponse:
    """Register a new user and return their details."""
    existing_user = get_user_by_email(db, email=payload.email.lower())
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.",
        )

    return create_user(db, payload, hashed_pw=hash_password(payload.password))


@router.post("/login")
def login_user(payload: UserLoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    """Authenticate user and return JWT token."""
    # Fetch user from DB by email
    user: User | None = get_user_by_email(db, payload.email.lower())

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or inactive user",
        )

    # Check password validity
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(access_token=access_token, token_type=TOKEN_TYPE_BEARER)
