"""Security-related utilities such as password hashing and token handling."""

from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core import get_settings

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load global settings (from config.py)
settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password (str): The user's plain-text password.

    Returns:
        str: A hashed version of the password.

    """
    return pwd_context.hash(password)


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
    to_encode.update({"exp": expire})

    # Encode token using secret and algorithm
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM,
    )
