"""Utility functions for testing user registration and login."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.responses import Response


def register(
    client: TestClient,
    email: str,
    password: str,
    full_name: str | None = None,
) -> Response:
    """Register a new user."""
    payload = {"email": email.strip(), "password": password}
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
