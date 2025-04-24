"""Security-related utilities such as password hashing and token handling."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.db.session import get_db
from app.core import get_settings
from app.crud.user import get_user_by_id
from app.core.redis import redis_client
from app.models.users.user import User
from app.models.users.activation_key import ActivationKey
import uuid
import re

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load global settings (from config.py)
settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
TOKEN_BLACKLIST_PREFIX = "blacklist:"

def create_activation_token(db: Session, user_id: int, ttl_minutes: int = 30) -> ActivationKey:
    """
    Create and store a secure one-time activation token for a user.
    """
    # Deactivate any old tokens
    db.query(ActivationKey).filter_by(user_id=user_id, is_active=True).update({"is_active": False})

    token = secrets.token_urlsafe(48)
    expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)

    activation = ActivationKey(
        user_id=user_id,
        key=token,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(activation)
    db.commit()
    db.refresh(activation)
    return activation


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password (str): The user's plain-text password.

    Returns:
        str: A hashed version of the password.

    """
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> bool:
    """
    Validates password strength.

    Rules:
    - Min 8 characters
    - At least one lowercase, uppercase, digit, special character
    """
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[\d]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one.

    Args:
        plain_password (str): Password input from user.
        hashed_password (str): Stored hash in the DB.

    Returns:
        bool: True if passwords match, else False.

    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(
        minutes=int(settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    ),
) -> str:
    """Generate a JWT access token with expiration.

    Args:
        data (dict): The payload data (e.g. {"sub": user_id}).
        expires_delta (timedelta, optional): How long the token should last.

    Returns:
        str: Encoded JWT token.

    """
    # Copy the payload and add expiration time
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta  # use timezone-aware datetime
    jti = str(uuid.uuid4())  # Generate unique token ID
    to_encode.update({"exp": expire, "jti": jti})

    # Encode token using secret and algorithm
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# --- JWT Decoder ---
def decode_access_token(token: str) -> dict:
    try:
        # Check Redis blacklist
        if redis_client.get(f"{TOKEN_BLACKLIST_PREFIX}{token}"):
            raise HTTPException(status_code=401, detail="Token has been revoked.")

        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        )


# --- Auth Dependency ---
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
)-> User:
    jti = get_token_jti(token)
    # Check Redis blacklist
    if redis_client.get(f"{TOKEN_BLACKLIST_PREFIX}{jti}"):
        raise HTTPException(status_code=401, detail="Token has been revoked.")

    # Decode JWT
    payload = decode_access_token(token)

    user_id_raw: Optional[int] = payload.get("sub")
    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    # Fetch user from DB
    user = get_user_by_id(db, user_id=int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Inactive or missing user.")

    return user


def get_token_jti(token: str) -> str:
    """
    Extract the 'jti' (JWT ID) from the given JWT access token.

    Args:
        token (str): JWT access token.

    Returns:
        str: The extracted 'jti' value.

    Raises:
        ValueError: If the token is invalid or 'jti' is missing.
    """
    try:
        payload = decode_access_token(token)
        jti = payload.get("jti")
        if not jti:
            raise ValueError("Token missing 'jti' claim.")
        return jti
    except JWTError as e:
        raise ValueError(f"Invalid JWT token: {str(e)}")
