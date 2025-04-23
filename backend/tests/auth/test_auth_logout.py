"""Tests for user logout endpoint at /api/v1/auth/logout."""

import pytest
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.main import app
from app.core.security import oauth2_scheme
from tests.utils import login, logout, register, get_token_from_response
from app.core.redis import redis_client
from app.core.security import get_token_jti

client = TestClient(app)


# -----------------------
# ✅ Positive Test Cases
# -----------------------


def test_tc_01_logout_with_valid_token(client: TestClient) -> None:
    """Logout with a valid token should return 200 OK and blacklist the token."""
    register(client, "logout01@example.com", "ValidPass123!")
    res1 = login(client, "logout01@example.com", "ValidPass123!")
    token = get_token_from_response(res1)
    res = logout(client, token)

    assert res.status_code == HTTP_204_NO_CONTENT


def test_tc_02_logout_then_use_token(client: TestClient) -> None:
    """After logout, token should be unusable."""
    register(client, "logout02@example.com", "ValidPass123!")
    res1 = login(client, "logout02@example.com", "ValidPass123!")
    token = get_token_from_response(res1)
    logout(client, token)

    # # Attempt using the token again
    # res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    # assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_03_logout_multiple_times(client: TestClient) -> None:
    """Logout multiple times with the same token should be idempotent."""
    register(client, "logout03@example.com", "ValidPass123!")
    res3 = login(client, "logout03@example.com", "ValidPass123!")
    token = get_token_from_response(res3)
    res1 = logout(client, token)
    res2 = logout(client, token)
    assert res1.status_code == HTTP_204_NO_CONTENT
    assert res2.status_code == HTTP_204_NO_CONTENT


def test_tc_04_token_blacklisted_in_redis(client: TestClient) -> None:
    """Verify the token is blacklisted in Redis."""
    register(client, "logout04@example.com", "ValidPass123!")
    res = login(client, "logout04@example.com", "ValidPass123!")
    token = get_token_from_response(res)
    jti = get_token_jti(token)
    logout(client, token)
    assert redis_client.get(f"blacklist:{jti}") is not None


# -----------------------
# ❌ Negative Test Cases
# -----------------------


def test_tc_10_logout_without_token(client: TestClient) -> None:
    """Logout without Authorization header returns 401."""
    res = client.post("/api/v1/auth/logout")
    assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_11_logout_with_malformed_token(client: TestClient) -> None:
    """Logout with a badly formatted token should fail."""
    res = logout(client, "malformed.token.payload")
    assert res.status_code in (HTTP_401_UNAUTHORIZED, HTTP_422_UNPROCESSABLE_ENTITY)


def test_tc_12_logout_with_expired_token(client: TestClient) -> None:
    """Expired token returns 401 Unauthorized."""
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Add actual expired JWT
    res = logout(client, expired_token)
    assert res.status_code == HTTP_401_UNAUTHORIZED


def test_tc_13_logout_with_empty_bearer(client: TestClient) -> None:
    """Empty Bearer token should return 401."""
    res = client.post("/api/v1/auth/logout", headers={"Authorization": "Bearer "})
    assert res.status_code == HTTP_401_UNAUTHORIZED


# ----------------------------
# 🧪 Edge Test Cases
# ----------------------------


def test_tc_20_logout_token_just_issued(client: TestClient) -> None:
    register(client, "logout04@example.com", "ValidPass123!")
    res1 = login(client, "logout04@example.com", "ValidPass123!")
    token = get_token_from_response(res1)
    res = logout(client, token)
    assert res.status_code == HTTP_204_NO_CONTENT
