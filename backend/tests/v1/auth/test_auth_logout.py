import pytest
from fastapi.testclient import TestClient
from starlette.status import HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED, HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY
from app.main import app
from tests.utils import register, login, get_token_from_response, make_email_str
from app.core import get_settings
from jose import jwt
from datetime import datetime, timedelta
from app.core.redis import redis_client

client = TestClient(app)
settings = get_settings()
AUTH_ENDPOINT = "/api/v1/auth/logout"

# -----------------------------
# ✅ Positive Test Cases
# -----------------------------

# TC_01 - Logout with valid token
def test_tc_01_logout_valid_token(client: TestClient):
    register(client, make_email_str("logout01"), "StrongPass123!")
    login_res = login(client, make_email_str("logout01"), "StrongPass123!")
    token = get_token_from_response(login_res)

    res = client.post(AUTH_ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == HTTP_204_NO_CONTENT

    # Token should now be blacklisted (Redis check optional)
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    jti = payload.get("jti")
    blacklisted = redis_client.get(f"blacklist:{jti}")
    assert blacklisted is not None
    assert blacklisted == "true"



# TC_02 - Logout with token already expired
def test_tc_02_logout_expired_token(client: TestClient):
    expired_token = jwt.encode(
        {"sub": "1", "exp": int((datetime.utcnow() - timedelta(minutes=1)).timestamp()), "jti": "expired-jti"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    res = client.post(AUTH_ENDPOINT, headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code in [HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED]


# TC_03 - Logout token reused after logout
def test_tc_03_logout_token_reuse(client: TestClient):
    register(client, make_email_str("reuse01"), "Secure123!")
    login_res = login(client, make_email_str("reuse01"), "Secure123!")
    token = get_token_from_response(login_res)

    client.post(AUTH_ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    reuse = client.post(AUTH_ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    assert reuse.status_code in [HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED]


# TC_04 - Logout multiple times with same token (idempotent)
def test_tc_04_logout_idempotent(client: TestClient):
    register(client, make_email_str("multi01"), "MultiPass123!")
    login_res = login(client, make_email_str("multi01"), "MultiPass123!")
    token = get_token_from_response(login_res)

    first = client.post(AUTH_ENDPOINT, headers={"Authorization": f"Bearer {token}"})
    second = client.post(AUTH_ENDPOINT, headers={"Authorization": f"Bearer {token}"})

    assert first.status_code == HTTP_204_NO_CONTENT
    assert second.status_code in [HTTP_204_NO_CONTENT, HTTP_401_UNAUTHORIZED]


# TC_05 - Logout with custom user-agent and request metadata
def test_tc_05_logout_with_custom_headers(client: TestClient):
    register(client, make_email_str("agent01"), "Agent123!")
    login_res = login(client, make_email_str("agent01"), "Agent123!")
    token = get_token_from_response(login_res)

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "TestClient/1.0",
        "X-Forwarded-For": "203.0.113.42"
    }

    res = client.post(AUTH_ENDPOINT, headers=headers)
    assert res.status_code == HTTP_204_NO_CONTENT

# -----------------------------
# ❌ Negative Test Cases
# -----------------------------
# TC_10 - Missing Authorization header
def test_tc_10_missing_auth_header(client: TestClient):
    res = client.post(AUTH_ENDPOINT)
    assert res.status_code == HTTP_401_UNAUTHORIZED


# TC_11 - Malformed token (not JWT format)
def test_tc_11_malformed_token(client: TestClient):
    headers = {"Authorization": "Bearer not.a.jwt"}
    res = client.post(AUTH_ENDPOINT, headers=headers)
    assert res.status_code in [HTTP_401_UNAUTHORIZED, HTTP_422_UNPROCESSABLE_ENTITY]


# TC_12 - Token missing jti claim
def test_tc_12_token_missing_jti(client: TestClient):
    token = jwt.encode(
        {"sub": "1", "exp": int((datetime.utcnow() + timedelta(minutes=5)).timestamp())},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(AUTH_ENDPOINT, headers=headers)
    assert res.status_code in [HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED]


# TC_13 - Token missing exp claim
def test_tc_13_token_missing_exp(client: TestClient):
    token = jwt.encode(
        {"sub": "1", "jti": "missing-exp-jti"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(AUTH_ENDPOINT, headers=headers)
    assert res.status_code == HTTP_401_UNAUTHORIZED


# TC_14 - Token with non-existent user ID
def test_tc_14_token_nonexistent_user(client: TestClient):
    # Use a high, unlikely user ID
    token = jwt.encode(
        {
            "sub": "9999999",
            "exp": int((datetime.utcnow() + timedelta(minutes=10)).timestamp()),
            "jti": "fakeuser-jti"
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(AUTH_ENDPOINT, headers=headers)
    assert res.status_code == HTTP_401_UNAUTHORIZED

# -----------------------
# 🔁 Corner Test Cases
# -----------------------
# def test_tc_30_logout_redis_unavailable(monkeypatch, client: TestClient, token_valid_user):
#     """Simulate Redis being unavailable during logout."""
#     monkeypatch.setattr("app.core.redis.redis_client.setex", lambda *a, **k: (_ for _ in ()).throw(ConnectionError("Redis down")))
#     res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token_valid_user}"})
#     assert res.status_code == 503

def test_tc_31_logout_ttl_logic_fail(client: TestClient):
    """JWT token missing `exp` should fail with TTL logic error."""
    token = jwt.encode({"sub": "1", "jti": "fail-ttl"}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

# def test_tc_32_token_already_blacklisted(client: TestClient, token_valid_user):
#     """Logging out with already-blacklisted token returns 204."""
#     client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token_valid_user}"})  # first logout
#     res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token_valid_user}"})  # second logout
#     assert res.status_code == 204

def test_tc_33_logout_refresh_token(client: TestClient):
    """Send refresh token instead of access token — should be rejected."""
    refresh_token = "Bearer this.is.a.refresh.token"
    res = client.post("/api/v1/auth/logout", headers={"Authorization": refresh_token})
    assert res.status_code == 401

# -----------------------
# 🔐 Security Test Cases
# -----------------------
# def test_tc_40_reuse_token_after_logout(client: TestClient, token_valid_user):
#     """Attempt to use token after logout — should be invalidated."""
#     client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token_valid_user}"})
#     res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_valid_user}"})
#     assert res.status_code == 401

def test_tc_41_jwt_tampered(client: TestClient):
    """JWT payload tampered — must be rejected."""
    token = jwt.encode({"sub": "1", "jti": "tampered"}, "WRONG_SECRET", algorithm=settings.JWT_ALGORITHM)
    res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

def test_tc_42_wrong_signing_key(client: TestClient):
    """JWT signed with incorrect secret key — reject it."""
    token = jwt.encode({"sub": "1", "exp": int((datetime.utcnow() + timedelta(minutes=10)).timestamp()), "jti": "invalid-key"}, "badkey", algorithm="HS256")
    res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401

def test_tc_43_xss_in_user_agent(client: TestClient):
    """User agent includes XSS attempt — ensure it's not executed/logged raw."""
    headers = {
        "Authorization": "Bearer fake.token.here",
        "User-Agent": "<script>alert(1)</script>"
    }
    res = client.post("/api/v1/auth/logout", headers=headers)
    assert res.status_code in (401, 422)

def test_tc_44_sql_injection_in_token(client: TestClient):
    """SQL injection payload in JWT — should not crash."""
    token = "' OR 1=1 --"
    res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in (401, 422)

# def test_tc_45_logout_bot_with_honeypot(client: TestClient):
#     email = "honeypot@example.com"
#     password = "StrongPass123!"
#     register(client, email, password)
#     login_res = login(client, email, password)
#     token = get_token_from_response(login_res)

#     headers = {
#         "Authorization": f"Bearer {token}",
#         "X-Honeypot": "I am a bot"
#     }

#     res = client.post("/api/v1/auth/logout", headers=headers)
#     assert res.status_code == 400


# def test_tc_46_password_not_logged(client: TestClient, caplog):
#     """Ensure password is not logged during logout."""
#     register(client, "nologs@example.com", "SuperSecret123!")
#     login_res = login(client, "nologs@example.com", "SuperSecret123!")
#     token = get_token_from_response(login_res)
#     with caplog.at_level("INFO"):
#         client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
#         logs = "\n".join(record.message for record in caplog.records)
#         assert "SuperSecret123!" not in logs
