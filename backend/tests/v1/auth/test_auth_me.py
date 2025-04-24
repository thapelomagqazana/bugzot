import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt
from uuid import uuid4

from app.core import get_settings
from app.models.users.user import User
from tests.utils import register, login, get_token_from_response
from app.db import TestingSessionLocal

settings = get_settings()

# ---------------------------
# ✅ POSITIVE TEST CASES
# ---------------------------

def test_get_me_valid_token_active_user(client: TestClient):
    register(client, "user1@example.com", "password123", "Active User")
    login_res = login(client, "user1@example.com", "password123")
    token = get_token_from_response(login_res)

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "user1@example.com"
    assert data["is_active"] is True


def test_get_me_valid_token_no_fullname(client: TestClient):
    register(client, "user2@example.com", "password123")
    login_res = login(client, "user2@example.com", "password123")
    token = get_token_from_response(login_res)

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "user2@example.com"
    assert data["full_name"] is None


def test_get_me_valid_token_all_fields(client: TestClient):
    register(client, "user3@example.com", "password123", "John Doe")
    login_res = login(client, "user3@example.com", "password123")
    token = get_token_from_response(login_res)

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "user3@example.com"
    assert data["full_name"] == "John Doe"
    assert "created_at" in data
    assert "updated_at" in data


# ---------------------------
# ❌ NEGATIVE TEST CASES
# ---------------------------

def test_get_me_missing_authorization_header(client: TestClient):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_get_me_malformed_token(client: TestClient):
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer abc.def"})
    assert res.status_code == 401


def test_get_me_expired_token(client: TestClient):
    # Manually craft expired token
    expired_payload = {
        "sub": "999",
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401


def test_get_me_deleted_user(client: TestClient, db_session: Session):
    register(client, "deleted@example.com", "password123")
    login_res = login(client, "deleted@example.com", "password123")
    token = get_token_from_response(login_res)

    user = db_session.query(User).filter(User.email == "deleted@example.com").first()
    user.is_deleted = True
    db_session.commit()

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_get_me_inactive_user(client: TestClient, db_session: Session):
    register(client, "inactive@example.com", "password123")
    login_res = login(client, "inactive@example.com", "password123")
    token = get_token_from_response(login_res)

    user = db_session.query(User).filter(User.email == "inactive@example.com").first()
    user.is_active = False
    db_session.commit()

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

# -----------------------------------
# ⚠️ EDGE CASE TESTS
# -----------------------------------
def test_me_user_with_null_last_login_and_zero_attempts(client: TestClient, db_session: Session):
    register(client, "noll@example.com", "password123")
    token = get_token_from_response(login(client, "noll@example.com", "password123"))

    user = db_session.query(User).filter(User.email == "noll@example.com").first()
    user.last_login = None
    user.login_attempts = 0
    db_session.commit()

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "noll@example.com"


def test_me_user_with_minimal_fields(client: TestClient):
    register(client, "minimal@example.com", "password123")
    token = get_token_from_response(login(client, "minimal@example.com", "password123"))

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    data = res.json()
    assert res.status_code == 200
    assert data["email"] == "minimal@example.com"
    assert data.get("full_name") is None


# -----------------------------------
# 🧱 CORNER CASE TESTS
# -----------------------------------

def test_me_token_valid_signature_invalid_payload(client: TestClient):
    register(client, "corner1@example.com", "password123")
    valid_token = get_token_from_response(login(client, "corner1@example.com", "password123"))
    decoded = jwt.decode(valid_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    decoded["sub"] = "invalid"

    token = jwt.encode(decoded, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_me_user_with_reporter_and_assignee_bugs(client: TestClient, db_session: Session):
    register(client, "dual@example.com", "password123")
    token = get_token_from_response(login(client, "dual@example.com", "password123"))
    user = db_session.query(User).filter(User.email == "dual@example.com").first()

    # Simulate relationships
    user.reported_bugs = []
    user.assigned_bugs = []
    db_session.commit()

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_me_user_created_now(client: TestClient, db_session: Session):
    email = "newuser@example.com"
    register(client, email, "password123")
    token = get_token_from_response(login(client, email, "password123"))

    user = db_session.query(User).filter(User.email == email).first()
    assert user.created_at is not None
    assert user.updated_at is None or user.updated_at == user.created_at

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


# -----------------------------------
# 🔒 SECURITY CASE TESTS
# -----------------------------------

def test_me_token_tampered_after_issue(client: TestClient):
    register(client, "tampered@example.com", "password123")
    token = get_token_from_response(login(client, "tampered@example.com", "password123"))
    tampered = token + "abc"

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert res.status_code == 401


def test_me_token_signed_with_wrong_key(client: TestClient):
    payload = {
        "sub": "123",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    wrong_key_token = jwt.encode(payload, "WRONG_SECRET", algorithm=settings.JWT_ALGORITHM)

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {wrong_key_token}"})
    assert res.status_code == 401


def test_me_token_with_sql_injection_payload(client: TestClient):
    payload = {
        "sub": "' OR 1=1 --",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "jti": str(uuid4())
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_me_token_of_another_user(client: TestClient):
    register(client, "user_a@example.com", "password123")
    token_a = get_token_from_response(login(client, "user_a@example.com", "password123"))

    register(client, "user_b@example.com", "password123")
    token_b = get_token_from_response(login(client, "user_b@example.com", "password123"))

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    data_a = res.json()
    assert data_a["email"] == "user_a@example.com"

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    data_b = res.json()
    assert data_b["email"] == "user_b@example.com"


@pytest.mark.skip(reason="Cannot test HTTP vs HTTPS in local FastAPI app")
def test_me_http_vs_https_access():
    """
    This should be tested in integration tests or with API Gateway/Ingress setup.
    App does not know the protocol.
    """
    pass
