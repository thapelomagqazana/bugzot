import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from jose import jwt
from tests.utils import (
    make_email_str,
    get_user_token_header,
    register,
    login,
    create_test_token,
)
from app.core import get_settings
from app.models.users.user import User

ENDPOINT = "/api/v1/users"
settings = get_settings()

# --------------------------
# Positive Test Cases
# --------------------------


# TC_01 - Admin deletes an active user
def test_tc_01_admin_deletes_active_user(client):
    email = make_email_str("activeuser")
    res1 = register(client, email, "Password123!", role_id=1)
    login(client, email, "Password123!")
    user_id = res1.json()["id"]

    admin_email = make_email_str("admin")
    register(client, admin_email, "Password123!", role_id=3)
    admin_res2 = login(client, admin_email, "Password123!")
    admin_token_header = get_user_token_header(admin_res2)

    response = client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == user_id
    assert response.json()["deleted_at"] is not None


# TC_02 - Admin deletes a user already soft-deleted
def test_tc_02_admin_deletes_already_soft_deleted_user(client):
    email = make_email_str("deleteduser")
    res1 = register(client, email, "Password123!", role_id=1)
    res2 = login(client, email, "Password123!")
    get_user_token_header(res2)
    user_id = res1.json()["id"]

    admin_email = make_email_str("admin2")
    register(client, admin_email, "Password123!", role_id=3)
    admin_res2 = login(client, admin_email, "Password123!")
    admin_token_header = get_user_token_header(admin_res2)

    # First delete (soft delete)
    client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token_header)

    # Second delete attempt
    response = client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token_header)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# TC_03 - Admin deletes an inactive user
def test_tc_03_admin_deletes_inactive_user(client):
    email = make_email_str("inactiveuser")
    res1 = register(client, email, "Password123!", role_id=1)
    res2 = login(client, email, "Password123!")
    get_user_token_header(res2)
    user_id = res1.json()["id"]

    admin_email = make_email_str("admin3")
    register(client, admin_email, "Password123!", role_id=3)
    admin_res2 = login(client, admin_email, "Password123!")
    admin_token_header = get_user_token_header(admin_res2)

    # Make user inactive manually
    client.put(
        f"{ENDPOINT}/{user_id}", headers=admin_token_header, json={"is_active": False}
    )

    response = client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token_header)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == user_id
    assert response.json()["deleted_at"] is not None


# --------------------------
# Negative Test Cases
# --------------------------


# TC_10 - Try to delete non-existent user
def test_tc_10_delete_non_existent_user(client):
    admin_email = make_email_str("admin4")
    register(client, admin_email, "Password123!", role_id=3)
    admin_res2 = login(client, admin_email, "Password123!")
    admin_token_header = get_user_token_header(admin_res2)

    response = client.delete(f"{ENDPOINT}/999999", headers=admin_token_header)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# TC_11 - Non-admin user tries to delete another user
def test_tc_11_non_admin_deletes_user(client):
    email1 = make_email_str("user1")
    register(client, email1, "Password123!", role_id=1)
    login1 = login(client, email1, "Password123!")
    user1_token = get_user_token_header(login1)

    email2 = make_email_str("user2")
    res2 = register(client, email2, "Password123!", role_id=1)
    user2_id = res2.json()["id"]

    response = client.delete(f"{ENDPOINT}/{user2_id}", headers=user1_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# TC_12 - Admin tries to delete their own account
def test_tc_12_admin_deletes_self(client):
    admin_email = make_email_str("selfadmin")
    res = register(client, admin_email, "Password123!", role_id=3)
    login_res = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(login_res)
    admin_id = res.json()["id"]

    response = client.delete(f"{ENDPOINT}/{admin_id}", headers=admin_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# TC_13 - Provide invalid id format (e.g., string instead of int)
def test_tc_13_delete_invalid_id_format(client):
    admin_email = make_email_str("admin5")
    register(client, admin_email, "Password123!", role_id=3)
    login_res = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(login_res)

    response = client.delete(f"{ENDPOINT}/invalid_id", headers=admin_token)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# TC_14 - Send DELETE with no ID (e.g., /users/)
def test_tc_14_delete_no_id(client):
    admin_email = make_email_str("admin6")
    register(client, admin_email, "Password123!", role_id=3)
    login_res = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(login_res)

    response = client.delete(f"{ENDPOINT}/", headers=admin_token)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# --------------------------
# Edge Test Cases
# --------------------------


# TC_20 - Delete user with id=0
def test_tc_20_delete_user_id_zero(client):
    admin_email = make_email_str("admin_edge0")
    register(client, admin_email, "Password123!", role_id=3)
    login_res = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(login_res)

    response = client.delete(f"{ENDPOINT}/0", headers=admin_token)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# TC_21 - Delete user with maximum allowed int ID (2^31-1)
def test_tc_21_delete_max_int_id(client):
    admin_email = make_email_str("admin_maxint")
    register(client, admin_email, "Password123!", role_id=3)
    login_res = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(login_res)

    max_id = 2**31 - 1
    response = client.delete(f"{ENDPOINT}/{max_id}", headers=admin_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# TC_22 - Delete user immediately after creating
def test_tc_22_delete_after_create(client):
    email = make_email_str("deletefast")
    res1 = register(client, email, "Password123!", role_id=3)
    login_res = login(client, email, "Password123!")
    get_user_token_header(login_res)
    user_id = res1.json()["id"]

    admin_email = make_email_str("admin_deletefast")
    register(client, admin_email, "Password123!", role_id=3)
    admin_login = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(admin_login)

    response = client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token)
    assert response.status_code == status.HTTP_200_OK


# TC_23 - Delete user with many related data (simulate)
def test_tc_23_delete_user_many_related(client):
    email = make_email_str("heavyuser")
    res1 = register(client, email, "Password123!", role_id=3)
    login(client, email, "Password123!")
    user_id = res1.json()["id"]

    # (Optional) Insert heavy related data: simulate 10k comments if you want

    admin_email = make_email_str("admin_heavy")
    register(client, admin_email, "Password123!", role_id=3)
    admin_login = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(admin_login)

    response = client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token)
    assert response.status_code == status.HTTP_200_OK


# --------------------------
# Corner Test Cases
# --------------------------


# TC_30 - Delete user deactivated (is_active=False)
def test_tc_30_delete_inactive_user(client):
    email = make_email_str("inactiveuser")
    res1 = register(client, email, "Password123!", role_id=3)
    login(client, email, "Password123!")
    user_id = res1.json()["id"]

    admin_email = make_email_str("admin_inactive")
    register(client, admin_email, "Password123!", role_id=3)
    admin_login = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(admin_login)

    # Simulate deactivate
    client.put(f"{ENDPOINT}/{user_id}", headers=admin_token, json={"is_active": False})

    response = client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token)
    assert response.status_code == status.HTTP_200_OK


# TC_31 - Delete user who never logged in
def test_tc_31_delete_never_logged_in(client):
    email = make_email_str("neverloginuser")
    res1 = register(client, email, "Password123!", role_id=3)
    user_id = res1.json()["id"]

    admin_email = make_email_str("admin_neverlogin")
    register(client, admin_email, "Password123!", role_id=3)
    admin_login = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(admin_login)

    response = client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token)
    assert response.status_code == status.HTTP_200_OK


# TC_32 - Delete user owning critical objects
def test_tc_32_delete_user_with_critical_objects(client):
    email = make_email_str("criticaluser")
    res1 = register(client, email, "Password123!", role_id=3)
    login(client, email, "Password123!")
    user_id = res1.json()["id"]

    admin_email = make_email_str("admin_critical")
    register(client, admin_email, "Password123!", role_id=3)
    admin_login = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(admin_login)

    # No special check for ownership, system must handle normally
    response = client.delete(f"{ENDPOINT}/{user_id}", headers=admin_token)
    assert response.status_code == status.HTTP_200_OK


# TC_33 - Admin deletes another admin
def test_tc_33_admin_deletes_admin(client):
    admin_email1 = make_email_str("adminone")
    res1 = register(client, admin_email1, "Password123!", role_id=3)
    login(client, admin_email1, "Password123!")
    admin1_id = res1.json()["id"]

    admin_email2 = make_email_str("admintwo")
    register(client, admin_email2, "Password123!", role_id=3)
    login_res2 = login(client, admin_email2, "Password123!")
    admin2_token = get_user_token_header(login_res2)

    response = client.delete(f"{ENDPOINT}/{admin1_id}", headers=admin2_token)
    assert response.status_code == status.HTTP_200_OK


# --------------------------
# Security Test Cases
# --------------------------


# TC_40 - No Authorization header
def test_tc_40_delete_no_auth(client):
    response = client.delete(f"{ENDPOINT}/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# TC_42 - Malformed/invalid JWT
def test_tc_42_delete_invalid_jwt(client):
    headers = {"Authorization": "Bearer invalid.token.here"}
    response = client.delete(f"{ENDPOINT}/1", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# TC_43 - Token of normal user tries delete
def test_tc_43_nonadmin_delete_attempt(client):
    email = make_email_str("normaluser")
    res1 = register(
        client, email, "Password123!", role_id=2
    )  # Reporter role, not Admin
    login_res = login(client, email, "Password123!")
    user_token = get_user_token_header(login_res)
    user_id = res1.json()["id"]

    response = client.delete(f"{ENDPOINT}/{user_id}", headers=user_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# TC_44 - SQL Injection attempt in ID
def test_tc_44_sql_injection_attempt(client):
    admin_email = make_email_str("admin_sql")
    register(client, admin_email, "Password123!", role_id=3)
    login_res = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(login_res)

    response = client.delete(f"{ENDPOINT}/1;DROP TABLE users;", headers=admin_token)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# TC_45 - Cross-tenant attack
def test_tc_45_cross_tenant_attack(client):
    # Assume different tenant separation, simple 404 simulation
    admin_email = make_email_str("tenant_admin")
    register(client, admin_email, "Password123!", role_id=3)
    login_res = login(client, admin_email, "Password123!")
    admin_token = get_user_token_header(login_res)

    response = client.delete(
        f"{ENDPOINT}/999999", headers=admin_token
    )  # ID not from their tenant
    assert response.status_code in [
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ]
