"""Tests for user registration endpoint at /api/v1/auth/register."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.responses import Response
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_409_CONFLICT,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.main import app
from tests.utils import (
    get_user_from_db,
    register,
)

client = TestClient(app)


# -----------------------
# ✅ Positive Test Cases
# -----------------------
def test_tc_01_register_valid_user(client: TestClient) -> None:
    """Register user with valid email, password, and full name."""
    res = register(client, "user1@example.com", "StrongPass123!", "Alice")
    assert res.status_code == HTTP_201_CREATED
    assert res.json()["email"] == "user1@example.com"


def test_tc_02_register_no_full_name(client: TestClient) -> None:
    """Register user without full_name field (should default to None or '')."""
    res = register(client, "user2@example.com", "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED
    assert res.json().get("full_name") in (None, "")


def test_tc_03_email_lowercase(client: TestClient) -> None:
    """Register user with mixed-case email (should normalize to lowercase)."""
    res = register(client, "User3@Example.COM", "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED
    assert res.json()["email"] == "user3@example.com"


def test_tc_04_default_role(client: TestClient) -> None:
    """Assign default role ID when user registers."""
    res = register(client, "user4@example.com", "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED
    assert res.json()["role_id"] == 1  # Adjust if default is different


# ------------------------
# ❌ Negative Test Cases
# ------------------------
def test_tc_05_duplicate_email(client: TestClient) -> None:
    """Reject registration if email is already registered."""
    register(client, "user5@example.com", "StrongPass123!")
    res = register(client, "user5@example.com", "AnotherPass!")
    assert res.status_code == HTTP_409_CONFLICT
    assert "already registered" in res.json()["detail"]


def test_tc_06_empty_email(client: TestClient) -> None:
    """Reject registration with empty email."""
    res = register(client, "", "StrongPass123!")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_07_empty_password(client: TestClient) -> None:
    """Reject registration with empty password."""
    res = register(client, "user7@example.com", "")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_08_short_password(client: TestClient) -> None:
    """Reject password shorter than minimum required length."""
    res: Response = register(client, "user8@example.com", "123")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_09_invalid_email_format(client: TestClient) -> None:
    """Reject invalid email formats (missing domain parts, etc)."""
    res: Response = register(client, "invalid-email", "StrongPass123!")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_10_long_full_name(client: TestClient) -> None:
    """Allow very long full names or reject if it exceeds DB max length."""
    long_name = "A" * 600
    res: Response = register(client, "user10@example.com", "StrongPass123!", long_name)
    assert res.status_code in [HTTP_201_CREATED, HTTP_422_UNPROCESSABLE_ENTITY]


# ---------------------
# 🌐 EDGE TEST CASES
# ---------------------


def test_tc_11_email_mixed_case(client: TestClient, db_session: Session) -> None:
    """Normalize and accept mixed-case emails."""
    res = register(client, "TestUser@Example.COM", "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED
    user = get_user_from_db(db_session, "testuser@example.com")
    assert user.email == "testuser@example.com"


def test_tc_12_password_special_chars_only(client: TestClient) -> None:
    """Accept passwords with only special characters."""
    res = register(client, "specialchar@example.com", "!@#$%^&*()")
    assert res.status_code == HTTP_201_CREATED


def test_tc_13_empty_full_name(client: TestClient) -> None:
    """Accept empty full_name field."""
    res = register(client, "emptyname@example.com", "StrongPass123!", "")
    assert res.status_code == HTTP_201_CREATED
    assert res.json()["full_name"] in [None, ""]


def test_tc_14_email_with_spaces(client: TestClient, db_session: Session) -> None:
    """Trim whitespace in email before storing."""
    res = register(client, "  user.space@example.com  ", "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED
    user = get_user_from_db(db_session, "user.space@example.com")
    assert user is not None


# ---------------------
# 🔲 CORNER TEST CASES
# ---------------------
@pytest.mark.skip(
    reason="Race condition requires transaction-safe locking or retry logic"
)
def test_tc_15_race_condition_same_email(client: TestClient) -> None:
    """Ensure registration race condition is handled correctly."""
    from concurrent.futures import ThreadPoolExecutor

    def attempt_register() -> Response:
        return register(client, "race@example.com", "StrongPass123!")

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: attempt_register(), range(2)))

    statuses = [res.status_code for res in results]
    assert HTTP_201_CREATED in statuses
    assert HTTP_409_CONFLICT in statuses


def test_tc_16_large_full_name(client: TestClient) -> None:
    """Reject extremely large full_name field."""
    long_name = "X" * 2_000_000
    res = register(client, "huge@example.com", "StrongPass123!", long_name)
    assert res.status_code in [
        HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        HTTP_422_UNPROCESSABLE_ENTITY,
        HTTP_400_BAD_REQUEST,
    ]


@pytest.mark.skip(reason="Reserved email check not implemented yet")
def test_tc_17_reserved_admin_email(client: TestClient) -> None:
    """Reject reserved email like admin@example.com."""
    res = register(client, "admin@example.com", "StrongPass123!")
    assert res.status_code in [HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY]
