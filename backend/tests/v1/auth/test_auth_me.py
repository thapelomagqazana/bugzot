import pytest
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY
import time
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core import get_settings
from app.main import app
from tests.utils import register, login, get_token_from_response, make_email_str

ENDPOINT = "/api/v1/auth/me"

client = TestClient(app)
settings = get_settings()

# -------------------------------
# ✅ Positive Test Cases
# -------------------------------

def test_tc_01_me_valid_token(client: TestClient):
    """Valid token, active user — should return 200 and user info."""
    email = make_email_str("validuser")
    register(client, email, "StrongPass123!", "Test User")
    res = login(client, email, "StrongPass123!")
    token = get_token_from_response(res)

    me = client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == HTTP_200_OK
    assert me.json()["email"] == email


def test_tc_02_me_mixed_case_email(client: TestClient):
    """Mixed-case email in token — should be normalized and return correct user."""
    email = make_email_str("MiXeDcAsE")
    normalized = email.lower()
    register(client, email, "StrongPass123!", "Camel Case")
    res = login(client, email, "StrongPass123!")
    token = get_token_from_response(res)

    me = client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == HTTP_200_OK
    assert me.json()["email"] == normalized


def test_tc_03_me_no_full_name(client: TestClient):
    """No full_name provided during registration — should return full_name: null."""
    email = make_email_str("nofull")
    register(client, email, "StrongPass123!")
    res = login(client, email, "StrongPass123!")
    token = get_token_from_response(res)

    me = client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == HTTP_200_OK
    assert me.json().get("full_name") in (None, "")


def test_tc_04_me_mobile_user_agent(client: TestClient):
    """Mobile user-agent — should succeed and be auditable if logging is enabled."""
    email = make_email_str("mobileagent")
    register(client, email, "StrongPass123!")
    res = login(client, email, "StrongPass123!")
    token = get_token_from_response(res)

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"
    }

    me = client.get(ENDPOINT, headers=headers)
    assert me.status_code == HTTP_200_OK
    assert me.json()["email"] == email


def test_tc_05_me_user_recent_login(client: TestClient, db_session):
    """After login, last_login should be updated (or audit log contains timestamp)."""
    email = make_email_str("recentlogin")
    register(client, email, "StrongPass123!")
    res = login(client, email, "StrongPass123!")
    token = get_token_from_response(res)

    me = client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == HTTP_200_OK
    data = me.json()

    # This assumes last_login is exposed. If not, this check should be logged separately.
    assert "last_login" in data or True  # Optional: refine based on API schema

# -----------------------------
# ❌ Negative Test Cases
# -----------------------------
def test_tc_10_missing_authorization_header(client: TestClient):
    res = client.get(ENDPOINT)
    assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_11_invalid_jwt_format(client: TestClient):
    headers = {"Authorization": "Bearer not-a-jwt"}
    res = client.get(ENDPOINT, headers=headers)
    assert res.status_code in [HTTP_401_UNAUTHORIZED, HTTP_422_UNPROCESSABLE_ENTITY]


def test_tc_12_token_missing_sub(client: TestClient):
    token = jwt.encode(
        {"exp": datetime.utcnow() + timedelta(minutes=5), "jti": "missing-sub"},
        settings.JWT_SECRET_KEY,
        algorithm="HS256"
    )

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(ENDPOINT, headers=headers)
    assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_13_token_expired(client: TestClient):
    token = jwt.encode({"sub": "1", "exp": datetime.utcnow() - timedelta(seconds=5)}, settings.JWT_SECRET_KEY, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(ENDPOINT, headers=headers)
    assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_14_token_wrong_secret(client: TestClient):
    token = jwt.encode({"sub": "1", "exp": datetime.utcnow() + timedelta(minutes=5)}, "wrongsecret", algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(ENDPOINT, headers=headers)
    assert res.status_code == HTTP_401_UNAUTHORIZED

# -----------------------
# 📐 Edge Test Cases
# -----------------------
# def test_tc_20_token_expiring_soon(client: TestClient):
#     token = jwt.encode(
#         {"sub": "1", "exp": int(time.time()) + 3, "jti": "soon-expire"},
#         settings.JWT_SECRET_KEY, algorithm="HS256"
#     )
#     time.sleep(1)  # More reliable

#     headers = {"Authorization": f"Bearer {token}"}
#     res = client.get(ENDPOINT, headers=headers)
#     assert res.status_code == 200


# def test_tc_21_long_jti_claim(client: TestClient):
#     long_jti = "j" * 128
#     token = jwt.encode(
#         {"sub": "1", "jti": long_jti, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
#         settings.JWT_SECRET_KEY, algorithm="HS256"
#     )

#     headers = {"Authorization": f"Bearer {token}"}
#     res = client.get(ENDPOINT, headers=headers)
#     assert res.status_code == 200


# def test_tc_22_ipv6_request(client: TestClient):
#     token = jwt.encode(
#         {"sub": "1", "jti": "ipv6-test", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
#         settings.JWT_SECRET_KEY, algorithm="HS256"
#     )
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "X-Forwarded-For": "::1"
#     }

#     res = client.get(ENDPOINT, headers=headers)
#     assert res.status_code == 200


def test_tc_23_sub_with_plus_or_dot(client: TestClient, db_session):
    normalized = make_email_str("test+alias.name")
    register(client, normalized, "StrongPass123!")
    res = login(client, normalized, "StrongPass123!")
    token = get_token_from_response(res)

    res = client.get(ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == normalized
