"""Test cases for the login endpoint (/api/v1/auth/login)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from tests.utils import login, register


# -----------------------
# ✅ Positive Test Cases
# -----------------------
def test_tc_01_login_valid_credentials(client: TestClient) -> None:
    """Login successfully with valid credentials."""
    register(client, "valid@example.com", "StrongPass123!")
    res = login(client, "valid@example.com", "StrongPass123!")

    assert res.status_code == HTTP_200_OK
    assert "access_token" in res.json()


def test_tc_02_login_mixed_case_email(client: TestClient) -> None:
    """Login successfully with mixed case email."""
    register(client, "mixedcase@example.com", "StrongPass123!")
    res = login(client, "MixedCase@Example.COM", "StrongPass123!")

    assert res.status_code == HTTP_200_OK
    assert "access_token" in res.json()


def test_tc_03_login_password_with_special_chars(client: TestClient) -> None:
    """Login successfully with special characters password."""
    register(client, "special@example.com", "Str0ng!@#$%^&*()")
    res = login(client, "special@example.com", "Str0ng!@#$%^&*()")

    assert res.status_code == HTTP_200_OK
    assert "access_token" in res.json()


def test_tc_04_login_user_with_full_name(client: TestClient) -> None:
    """Login successfully with full name."""
    register(client, "fullname@example.com", "StrongPass123!", full_name="John Doe")
    res = login(client, "fullname@example.com", "StrongPass123!")

    assert res.status_code == HTTP_200_OK
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# ------------------------
# ❌ Negative Test Cases
# ------------------------
def test_tc_05_login_email_not_found(client: TestClient) -> None:
    """Reject login for unregistered email."""
    res = login(client, "notfound@example.com", "StrongPass123!")
    assert res.status_code == HTTP_401_UNAUTHORIZED
    assert "Invalid credentials" in res.json()["detail"]


def test_tc_06_login_wrong_password(client: TestClient) -> None:
    """Reject login for wrong password."""
    register(client, "wrongpass@example.com", "CorrectPassword123!")
    res = login(client, "wrongpass@example.com", "WrongPassword")
    assert res.status_code == HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Invalid credentials"


def test_tc_07_login_empty_email(client: TestClient) -> None:
    """Reject login for empty email."""
    res = login(client, "", "StrongPass123!")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_08_login_empty_password(client: TestClient) -> None:
    """Reject login for empty password."""
    res = login(client, "empty@password.com", "")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_09_login_invalid_email_format(client: TestClient) -> None:
    """Reject login for invalid email."""
    res = login(client, "invalid-email", "StrongPass123!")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------
# 🌐 EDGE TEST CASES
# ---------------------
def test_tc_10_login_email_with_spaces(client: TestClient) -> None:
    """Accept email with whitespaces."""
    email = "  spaced@example.com  "
    password = "StrongPass123!"
    register(client, email.strip(), password)
    res = login(client, email, password)
    assert res.status_code in [HTTP_200_OK, HTTP_401_UNAUTHORIZED]


def test_tc_11_password_exactly_8_chars(client: TestClient) -> None:
    """Accept password that is exactly 8 characters."""
    email = "eightchar@example.com"
    password = "8Chars!!"
    register(client, email, password)
    res = login(client, email, password)
    assert res.status_code == HTTP_200_OK
    assert "access_token" in res.json()


def test_tc_12_email_with_subdomain(client: TestClient) -> None:
    """Allow login with subdomain email."""
    email = "user@mail.example.com"
    password = "StrongPass123!"
    register(client, email, password)
    res = login(client, email, password)
    assert res.status_code == HTTP_200_OK
    assert "access_token" in res.json()


def test_tc_13_password_with_unicode(client: TestClient) -> None:
    """Accept or reject passwords with Unicode characters."""
    email = "unicode@example.com"
    password = "P@ssw🔒rd!"
    register(client, email, password)
    res = login(client, email, password)
    assert res.status_code in [HTTP_200_OK, HTTP_401_UNAUTHORIZED]


# ---------------------
# 🔲 CORNER TEST CASES
# ---------------------
def test_tc_14_extremely_long_email(client: TestClient) -> None:
    """Reject or fail login with email > 200 chars."""
    long_email = f"{'a'*190}@example.com"
    password = "StrongPass123!"
    res = login(client, long_email, password)
    assert res.status_code in [HTTP_401_UNAUTHORIZED, HTTP_422_UNPROCESSABLE_ENTITY]


def test_tc_15_extremely_long_password(client: TestClient) -> None:
    """Handle login attempt with very long password (1000+ chars)."""
    email = "longpass@example.com"
    long_password = "A" * 1001
    res = login(client, email, long_password)
    assert res.status_code in [HTTP_401_UNAUTHORIZED, HTTP_422_UNPROCESSABLE_ENTITY]


# ---------------------
# SECURITY TEST CASES
# ---------------------
def test_tc_16_sql_injection_email(client: TestClient) -> None:
    """Prevent SQL injection via email."""
    res = login(client, "' OR 1=1--", "password")
    assert res.status_code in [HTTP_401_UNAUTHORIZED, HTTP_422_UNPROCESSABLE_ENTITY]


def test_tc_17_sql_injection_password(client: TestClient) -> None:
    """Prevent SQL injection via password."""
    email = "sqlinj@example.com"
    legit_password = "legitpassword"
    register(client, email, legit_password)
    res = login(client, email, "' OR 'a'='a")
    assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_18_token_does_not_expose_sensitive_data(client: TestClient) -> None:
    """Ensure JWT token does not expose sensitive user fields."""
    email = "privacy@example.com"
    password = "StrongPass123!"
    register(client, email, password)
    res = login(client, email, password)
    token = res.json()["access_token"]
    assert "password" not in token
    assert "hashed_password" not in token


def test_tc_20_disabled_user_login(client: TestClient, db_session: Session) -> None:
    """Reject login attempt for disabled/deleted user."""
    from app.models.users.user import User

    email = "disabled@example.com"
    password = "StrongPass123!"
    register(client, email, password)

    # Disable user manually
    user = db_session.query(User).filter(User.email == email.lower()).first()
    user.is_active = False
    db_session.commit()

    res = login(client, email, password)
    assert res.status_code in [HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN]
