"""Utility functions for testing user registration and login."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.responses import Response
from jose import jwt
import time
from datetime import datetime, timedelta
from app.core import get_settings

settings = get_settings()


def make_email_str(username: str) -> str:
    return f"{username}@protonmail.com"


def register(
    client: TestClient,
    email: str,
    password: str,
    full_name: str | None = None,
    role_id: int = 1,
    active: bool = True,
) -> Response:
    """Register a new user with optional role_id (for testing purposes)."""
    payload = {
        "email": email.strip(),
        "password": password,
        "role_id": role_id,
        "active": active,
    }
    if full_name is not None:
        payload["full_name"] = full_name
    return client.post("/api/v1/auth/register", json=payload)


def login(client: TestClient, email: str, password: str) -> Response:
    """Log in a user."""
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def get_user_from_db(db: Session, email: str) -> object | None:
    """Fetch user from the database by email."""
    from app.models.users.user import User

    return db.query(User).filter(User.email == email.lower()).first()


def login(client: TestClient, email: str, password: str):
    """
    Send a login request.

    Args:
        client (TestClient): FastAPI test client.
        email (str): User email.
        password (str): User password.

    Returns:
        Response: The HTTP response from the login endpoint.
    """
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )


def logout(client: TestClient, token: str):
    """
    Send a logout request.

    Args:
        client (TestClient): FastAPI test client.
        token (str): Bearer JWT token.

    Returns:
        Response: The HTTP response from the logout endpoint.
    """
    return client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
    )


def get_token_from_response(res) -> str:
    """
    Extract access token from login response.

    Args:
        res (Response): Login response.

    Returns:
        str: Access token from the response.
    """
    return res.json()["access_token"]


def get_admin_token_header(res):
    return {"Authorization": f"Bearer {res.json()["access_token"]}"}


def get_user_token_header(res):
    return {"Authorization": f"Bearer {res.json()["access_token"]}"}


def create_test_token(user_id: int, expire_in_minutes: int = 15, secret_override: str = None) -> str:
    """
    Helper function to create a JWT token for testing purposes.
    
    Args:
        user_id (int): ID of the user for whom the token is generated.
        expire_in_minutes (int): Minutes after which the token expires. Defaults to 15 minutes.
        secret_override (str): If provided, use this instead of default secret (used for invalid signature tests).

    Returns:
        str: Encoded JWT token.
    """
    secret = secret_override or settings.JWT_SECRET_KEY
    now = datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "exp": now + timedelta(minutes=expire_in_minutes),
        "iat": now,
        "jti": f"test-jti-{time.time()}"  # simple unique jti
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token
