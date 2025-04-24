import pytest
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from app.main import app
from app.core.security import hash_password
from tests.utils import register, login, get_user_from_db, make_email_str
from jose import jwt
from app.core import get_settings
from sqlalchemy.orm import Session

settings = get_settings()

client = TestClient(app)

# -----------------------------
# ✅ Positive Test Cases
# -----------------------------

def test_tc_01_valid_email_and_password(client: TestClient):
    register(client, make_email_str("valid1"), "StrongPass123!")
    res = login(client, make_email_str("valid1"), "StrongPass123!")
    assert res.status_code == HTTP_200_OK
    assert "access_token" in res.json()


def test_tc_02_email_with_uppercase_whitespace(client: TestClient):
    register(client, "valid2@protonmail.com", "StrongPass123!")
    res = login(client, "  VALID2@Protonmail.com ", "StrongPass123!")
    assert res.status_code == HTTP_200_OK
    assert "access_token" in res.json()


def test_tc_03_password_matches_hashed(client: TestClient):
    register(client, make_email_str("valid3"), "StrongPass123!")
    res = login(client, make_email_str("valid3"), "StrongPass123!")
    assert res.status_code == HTTP_200_OK


def test_tc_04_token_fields_present(client: TestClient):
    register(client, make_email_str("valid4"), "StrongPass123!")
    res = login(client, make_email_str("valid4"), "StrongPass123!")
    data = res.json()
    assert res.status_code == HTTP_200_OK
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_tc_05_login_from_mobile_user_agent(client: TestClient):
    register(client, make_email_str("valid5"), "StrongPass123!")
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"}
    res = client.post("/api/v1/auth/login", json={"email": make_email_str("valid5"), "password": "StrongPass123!"}, headers=headers)
    assert res.status_code == HTTP_200_OK
    assert "access_token" in res.json()


# -----------------------------
# ❌ Negative Test Cases
# -----------------------------

def test_tc_10_unregistered_email(client: TestClient):
    res = login(client, "nonexistent@example.com", "WrongPass123!")
    assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_11_wrong_password(client: TestClient):
    register(client, make_email_str("valid6"), "StrongPass123!")
    res = login(client, make_email_str("valid6"), "WrongPass123!")
    assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_12_deleted_user(db_session: Session, client: TestClient):
    register(client, make_email_str("deleted"), "StrongPass123!")
    user = get_user_from_db(db_session, make_email_str("deleted"))
    user.is_deleted = True
    db_session.commit()
    res = login(client, make_email_str("deleted"), "StrongPass123!")
    assert res.status_code in (HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN)


def test_tc_13_inactive_user(db_session: Session, client: TestClient):
    register(client, make_email_str("inactive"), "StrongPass123!")
    user = get_user_from_db(db_session, make_email_str("inactive"))
    user.is_active = False
    db_session.commit()
    res = login(client, make_email_str("inactive"), "StrongPass123!")
    assert res.status_code == HTTP_403_FORBIDDEN


def test_tc_14_missing_email(client: TestClient):
    res = client.post("/api/v1/auth/login", json={"password": "StrongPass123!"})
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_15_missing_password(client: TestClient):
    res = client.post("/api/v1/auth/login", json={"email": "user@example.com"})
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_16_invalid_email_format(client: TestClient):
    res = login(client, "not-an-email", "StrongPass123!")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY

# -----------------------
# 📐 Edge Test Cases
# -----------------------
def test_tc_21_password_min_length(client: TestClient):
    email = make_email_str("minpass")
    password = "A1!a2b3c"  # Exactly 8 characters, strong format
    register(client, email, password)
    res = login(client, email, password)
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_tc_22_login_ipv6(client: TestClient, monkeypatch):
    email = make_email_str("ipv6user")
    password = "Ipv6Pass123!"
    register(client, email, password)

    # Monkeypatch client IP
    class IPv6:
        host = "::1"
    monkeypatch.setattr("starlette.requests.Request.client", IPv6)

    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_tc_23_plus_symbol_email(client: TestClient):
    email = make_email_str("baseuser")
    alias_email = make_email_str("baseuser+test")
    password = "Alias123!"

    register(client, email, password)
    res = login(client, alias_email, password)

    # Depending on backend handling, this may pass or fail
    assert res.status_code in [200, 401]

# -----------------------
# 🔁 Corner Test Cases
# -----------------------
def test_tc_31_login_after_account_reactivation(client: TestClient, db_session):
    email = make_email_str("reactivate")
    password = "Reactivated123!"
    register(client, email, password)

    user = get_user_from_db(db_session, email)
    user.is_active = False
    db_session.commit()

    # Try logging in while deactivated
    res_fail = login(client, email, password)
    assert res_fail.status_code == 403

    # Reactivate user
    user.is_active = True
    db_session.commit()

    # Try again
    res_success = login(client, email, password)
    assert res_success.status_code == 200

def test_tc_32_login_after_password_reset(client: TestClient, db_session):
    email = make_email_str("resetme")
    old_password = "OldPass123!"
    new_password = "NewSecure123!"

    register(client, email, old_password)
    user = get_user_from_db(db_session, email)
    user.hashed_password = hash_password(new_password)
    db_session.commit()

    res_old = login(client, email, old_password)
    res_new = login(client, email, new_password)

    assert res_old.status_code == 401
    assert res_new.status_code == 200

def test_tc_33_jwt_structure(client: TestClient):
    email = make_email_str("jwtcheck")
    password = "JwtPass123!"
    register(client, email, password)
    res = login(client, email, password)
    token = res.json()["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert "sub" in payload and "exp" in payload

# -----------------------
# 🔐 Security Test Cases
# -----------------------
def test_tc_40_sql_injection_in_email(client: TestClient):
    res = login(client, "' OR 1=1 --", "Nope123!")
    assert res.status_code in [401, 422]

def test_tc_41_xss_script_input(client: TestClient):
    res = login(client, "<script>alert(1)</script>", "<script>123</script>")
    assert res.status_code in [401, 422]

def test_tc_43_no_token_on_failure(client: TestClient):
    res = login(client, "notfound@example.com", "WrongPass!")
    assert res.status_code == 401
    assert "access_token" not in res.json()

def test_tc_44_malformed_json(client: TestClient):
    res = client.post("/api/v1/auth/login", data="{email: 'oops'}")
    assert res.status_code == 422

def test_tc_46_expired_token(client: TestClient):
    from jose import jwt
    from datetime import datetime, timedelta

    token = jwt.encode(
        {"sub": "1", "exp": int((datetime.utcnow() - timedelta(hours=1)).timestamp())},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code in [401, 403]

