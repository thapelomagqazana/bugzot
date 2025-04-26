from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.core import get_settings
from tests.utils import (
    register,
    login,
    get_user_from_db,
    make_email_str,
    get_admin_token_header,
)

client = TestClient(app)
settings = get_settings()
ENDPOINT = "/api/v1/users"


def generate_token(
    payload: dict, secret: str = settings.JWT_SECRET_KEY, expire_in_minutes=5
):
    payload = payload.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expire_in_minutes)
    payload.setdefault("jti", "dummy-jti-1234")
    return jwt.encode(payload, secret, algorithm="HS256")


# -----------------------
# ✅ Positive Test Cases
# -----------------------
def test_tc_01_admin_valid_token_users_list(client: TestClient):
    email = make_email_str("adminuser")
    register(client, email, "StrongPass123!", role_id=3)
    res1 = login(client, email, "StrongPass123!")
    res = client.get(ENDPOINT, headers=get_admin_token_header(res1))
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)


def test_tc_02_admin_with_pagination(client: TestClient):
    email = make_email_str("adminuser")
    register(client, email, "StrongPass123!", role_id=3)
    res1 = login(client, email, "StrongPass123!")
    res = client.get(
        f"{ENDPOINT}?limit=10&skip=0", headers=get_admin_token_header(res1)
    )
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)
    assert len(res.json()["data"]) <= 10


def test_tc_03_admin_filter_active_users(client: TestClient):
    email = make_email_str("adminuser")
    register(client, email, "StrongPass123!", role_id=3)
    res1 = login(client, email, "StrongPass123!")
    res = client.get(f"{ENDPOINT}?is_active=true", headers=get_admin_token_header(res1))
    assert res.status_code == 200
    assert all(user["is_active"] is True for user in res.json()["data"])


def test_tc_05_admin_role_nested_in_response(client: TestClient):
    email = make_email_str("adminuser")
    register(client, email, "StrongPass123!", role_id=3)
    res1 = login(client, email, "StrongPass123!")
    res = client.get(ENDPOINT, headers=get_admin_token_header(res1))
    assert res.status_code == 200
    for user in res.json()["data"]:
        assert "role_id" in user
        assert isinstance(user["role_id"], int)


def test_tc_06_admin_pagination_limit_1(client: TestClient):
    email = make_email_str("adminuser")
    register(client, email, "StrongPass123!", role_id=3)
    res1 = login(client, email, "StrongPass123!")
    res = client.get(f"{ENDPOINT}?limit=1", headers=get_admin_token_header(res1))
    assert res.status_code == 200
    assert len(res.json()["data"]) <= 1


def test_tc_07_admin_filter_inactive_users(client: TestClient):
    email = make_email_str("adminuser")
    register(client, email, "StrongPass123!", role_id=3)
    res1 = login(client, email, "StrongPass123!")
    res = client.get(
        f"{ENDPOINT}?is_active=false", headers=get_admin_token_header(res1)
    )
    assert res.status_code == 200
    assert all(user["is_active"] is False for user in res.json()["data"])


# -----------------------
# ❌ Negative Test Cases
# -----------------------


def test_tc_10_missing_authorization_header(client: TestClient):
    res = client.get(ENDPOINT)
    assert res.status_code == 401


def test_tc_11_token_not_jwt(client: TestClient):
    headers = {"Authorization": "Bearer not.a.jwt.token"}
    res = client.get(ENDPOINT, headers=headers)
    assert res.status_code in (401, 422)


def test_tc_12_token_expired(client: TestClient):
    token = generate_token(
        {"sub": "admin@example.com", "role": "admin"}, expire_in_minutes=-1
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(ENDPOINT, headers=headers)
    assert res.status_code == 401


def test_tc_13_token_wrong_secret(client: TestClient):
    token = generate_token(
        {"sub": "admin@example.com", "role": "admin"}, secret="wrong_secret_key"
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(ENDPOINT, headers=headers)
    assert res.status_code == 401


def test_tc_14_non_admin_user_token(client: TestClient):
    token = generate_token({"sub": "user@example.com", "role": "user"})
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(ENDPOINT, headers=headers)
    print(res.json())
    assert res.status_code == 401


def test_tc_15_admin_malformed_query(client: TestClient):
    token = generate_token({"sub": "admin@example.com", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(f"{ENDPOINT}?limit=-1", headers=headers)
    assert res.status_code == 401


# -----------------------
# 📐 Edge Test Cases
# -----------------------
def test_tc_20_limit_zero_valid_admin(client: TestClient):
    email = make_email_str("adminuser")
    register(client, email, "StrongPass123!", role_id=3)
    res1 = login(client, email, "StrongPass123!")
    res = client.get(f"{ENDPOINT}?limit=0", headers=get_admin_token_header(res1))
    assert res.status_code == 200
    assert res.json()["data"] == []


# def test_tc_21_skip_beyond_user_count(client: TestClient):
#     email = make_email_str("adminuser")
#     register(client, email, "StrongPass123!", role_id=3)
#     res1 = login(client, email, "StrongPass123!")
#     res = client.get(f"{ENDPOINT}?skip=1000", headers=get_admin_token_header(res1))
#     assert res.status_code == 200
#     assert res.json()["data"] == []
