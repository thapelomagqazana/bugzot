import pytest
from fastapi import status
from starlette.testclient import TestClient
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core import get_settings
from tests.utils import (
    register,
    login,
    get_admin_token_header,
    make_email_str,
    get_user_token_header,
)

settings = get_settings()

ENDPOINT = "/api/v1/users"

# --------------------------
# Positive Test Cases
# --------------------------


def test_tc_01_admin_valid_token_existing_user(client: TestClient, db_session):
    email = make_email_str("adminuser")
    res1 = register(client, email, "AdminPass123!", role_id=3)
    res = login(client, email, "AdminPass123!")
    token_header = get_admin_token_header(res)
    user_id = res1.json()["id"]

    response = client.get(f"{ENDPOINT}/{user_id}", headers=token_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == user_id
    assert response.json()["email"] == email


def test_tc_02_admin_self_profile_retrieval(client: TestClient, db_session):
    email = make_email_str("selfadmin")
    res1 = register(client, email, "SelfPass123!", role_id=3)
    res = login(client, email, "SelfPass123!")
    token_header = get_admin_token_header(res)
    user_id = res1.json()["id"]

    response = client.get(f"{ENDPOINT}/{user_id}", headers=token_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == email


def test_tc_03_admin_user_no_full_name(client: TestClient, db_session):
    email = make_email_str("nofullnameadmin")
    res1 = register(client, email, "NoNamePass123!", role_id=3)
    res = login(client, email, "NoNamePass123!")
    token_header = get_admin_token_header(res)
    user_id = res1.json()["id"]

    response = client.get(f"{ENDPOINT}/{user_id}", headers=token_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] is None


def test_tc_04_admin_user_recently_created(client: TestClient, db_session):
    email = make_email_str("recentadmin")
    res1 = register(client, email, "RecentPass123!", role_id=3)
    res = login(client, email, "RecentPass123!")
    token_header = get_admin_token_header(res)
    user_id = res1.json()["id"]

    response = client.get(f"{ENDPOINT}/{user_id}", headers=token_header)
    created_at = datetime.fromisoformat(
        response.json()["created_at"].replace("Z", "+00:00")
    )

    assert response.status_code == status.HTTP_200_OK
    assert (datetime.now(timezone.utc) - created_at).seconds < 120


def test_tc_05_admin_user_special_email(client: TestClient, db_session):
    special_email = f"special.alias+{make_email_str('admin')}"
    res1 = register(client, special_email, "SpecialPass123!", role_id=3)
    res = login(client, special_email, "SpecialPass123!")
    token_header = get_admin_token_header(res)
    user_id = res1.json()["id"]

    response = client.get(f"{ENDPOINT}/{user_id}", headers=token_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"].startswith("special.alias+")


# --------------------------
# Negative Test Cases
# --------------------------


def test_tc_10_missing_authorization_header(client: TestClient):
    response = client.get(f"{ENDPOINT}/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tc_11_malformed_bearer_token(client: TestClient):
    headers = {"Authorization": "Bearer not.a.valid.token"}
    response = client.get(f"{ENDPOINT}/1", headers=headers)
    assert response.status_code in {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    }


def test_tc_12_expired_token(client: TestClient):
    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            "jti": "expiredjti",
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get(f"{ENDPOINT}/1", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tc_13_wrong_secret_token(client: TestClient):
    fake_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "jti": "fakejti",
        },
        "wrongsecret",
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {fake_token}"}
    response = client.get(f"{ENDPOINT}/1", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_tc_14_user_id_not_found(client: TestClient, db_session):
    email = make_email_str("adminfor404")
    register(client, email, "Admin404Pass!", role_id=3)
    res = login(client, email, "Admin404Pass!")
    token_header = get_admin_token_header(res)

    response = client.get(f"{ENDPOINT}/999999", headers=token_header)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_tc_15_non_admin_user_access_denied(client: TestClient, db_session):
    email = make_email_str("regularuser")
    register(client, email, "UserPass123!", role_id=2)  # Assume role_id=2 is non-admin
    res = login(client, email, "UserPass123!")
    token_header = get_user_token_header(res)

    response = client.get(f"{ENDPOINT}/1", headers=token_header)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_tc_16_soft_deleted_user(client: TestClient, db_session):
    # Assume you have a fixture or helper that creates a deleted user
    email = make_email_str("softdelete")
    res1 = register(client, email, "SoftDeletePass123!", role_id=3)
    login(client, email, "SoftDeletePass123!")
    user_id = res1.json()["id"]

    # Now soft-delete manually in DB
    from app.models.users.user import User

    user = db_session.query(User).filter(User.id == user_id).first()
    user.is_deleted = True
    db_session.commit()

    admin_email = make_email_str("adminfordeleted")
    register(client, admin_email, "AdminDeletePass123!", role_id=3)
    admin_res = login(client, admin_email, "AdminDeletePass123!")
    token_header = get_admin_token_header(admin_res)

    response = client.get(f"{ENDPOINT}/{user_id}", headers=token_header)
    assert response.status_code in {
        status.HTTP_404_NOT_FOUND,
        status.HTTP_403_FORBIDDEN,
    }


# --------------------------
# Edge Test Cases
# --------------------------


def test_tc_20_user_id_zero(client: TestClient):
    admin_email = make_email_str("adminfordeleted")
    register(client, admin_email, "AdminDeletePass123!", role_id=3)
    admin_res = login(client, admin_email, "AdminDeletePass123!")
    token_header = get_admin_token_header(admin_res)
    res = client.get(f"{ENDPOINT}/0", headers=token_header)
    assert res.status_code == 422


def test_tc_21_very_large_user_id(client: TestClient):
    admin_email = make_email_str("adminfordeleted")
    register(client, admin_email, "AdminDeletePass123!", role_id=3)
    admin_res = login(client, admin_email, "AdminDeletePass123!")
    token_header = get_admin_token_header(admin_res)
    res = client.get(f"{ENDPOINT}/99999999", headers=token_header)
    assert res.status_code == 404


def test_tc_23_user_id_off_by_one(client: TestClient):
    admin_email = make_email_str("adminfordeleted")
    register(client, admin_email, "AdminDeletePass123!", role_id=3)
    admin_res = login(client, admin_email, "AdminDeletePass123!")
    token_header = get_admin_token_header(admin_res)
    res = client.get(
        f"{ENDPOINT}/10", headers=token_header
    )  # Assume no user with ID 10
    assert res.status_code == 404


def test_tc_24_minimal_payload_token(client: TestClient):
    token = jwt.encode(
        {
            "sub": "1",
            "jti": "minimal",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(f"{ENDPOINT}/1", headers=headers)
    if res.status_code == 200:
        assert "email" in res.json()
    else:
        assert res.status_code == 401


# --------------------------
# Security Test Cases
# --------------------------
def test_tc_40_sql_injection_in_token_sub(client: TestClient):
    token = jwt.encode(
        {
            "sub": "1' OR '1'='1",
            "jti": "sqlinject",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(f"{ENDPOINT}/1", headers=headers)
    assert res.status_code == 401


def test_tc_41_xss_payload_in_token(client: TestClient):
    token = jwt.encode(
        {
            "sub": "1",
            "full_name": "<script>alert('xss')</script>",
            "jti": "xss",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(f"{ENDPOINT}/1", headers=headers)
    assert "<script>" not in res.text  # Output sanitized
