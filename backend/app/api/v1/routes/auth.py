"""Routes for managing auth-related operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.constants import TOKEN_TYPE_BEARER
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user,
    decode_access_token,
    oauth2_scheme,
    get_token_jti,
)
from app.crud.user import create_user, get_user_by_email
from app.core.redis import redis_client
from jose import jwt
from app.db.session import get_db
from app.core import get_settings

from app.models.users.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from datetime import datetime

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserRegisterRequest, db: Annotated[Session, Depends(get_db)]
) -> UserResponse:
    """Register a new user and return their details."""
    existing_user = get_user_by_email(db, email=payload.email.lower())
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    return create_user(db, payload, hashed_pw=hash_password(payload.password))


@router.post("/login")
def login_user(
    payload: UserLoginRequest, db: Annotated[Session, Depends(get_db)]
) -> TokenResponse:
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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Logout the current user by blacklisting the JWT token.
    """
    # Determine the token expiration time
    jti = get_token_jti(token)
    payload = decode_access_token(token)
    exp_timestamp = payload.get("exp")
    if not exp_timestamp:
        raise HTTPException(status_code=400, detail="Token missing expiration")

    ttl = exp_timestamp - int(datetime.utcnow().timestamp())

    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis unavailable"
        )

    # Blacklist the token in Redis
    redis_client.setex(f"blacklist:{jti}", ttl, "true")

    return {"detail": "Successfully logged out."}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Retrieve details of the currently authenticated user.
    """
    return current_user
