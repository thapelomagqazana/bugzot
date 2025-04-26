"""Utility functions for testing user registration and login."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.responses import Response


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
