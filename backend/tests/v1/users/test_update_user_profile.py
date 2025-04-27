import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from jose import jwt
from tests.utils import (
    make_email_str, 
    get_user_token_header,
    register, login,
    create_test_token
)
from app.core import get_settings
from app.models.users.user import User

ENDPOINT = "/api/v1/users"
settings = get_settings()

# --------------------------
# Positive Test Cases
# --------------------------

# TC_01 - Update valid full_name only
def test_tc_01_update_valid_full_name(client):
    email = make_email_str("fullnameuser")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": "Updated Name"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] == "Updated Name"

# TC_02 - Update valid email only
def test_tc_02_update_valid_email(client):
    email = make_email_str("emailuser")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    new_email = make_email_str("updatedemail")
    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"email": new_email})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == new_email

# TC_03 - Update valid role_id (admin only)
def test_tc_03_update_valid_role_id_admin(client):
    email = make_email_str("adminchanger")
    res1 = register(client, email, "Password123!", role_id=3)  # Admin user
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)  # Ensure admin privileges
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"role_id": 2})  # Update role to "moderator" maybe
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["role_id"] == 2

# TC_04 - Update both full_name and email together
def test_tc_04_update_full_name_and_email(client):
    email = make_email_str("bothchanger")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    new_full_name = "Full Name Updated"
    new_email = make_email_str("newemail")
    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={
        "full_name": new_full_name,
        "email": new_email
    })
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] == new_full_name
    assert response.json()["email"] == new_email

# TC_06 - Update with minimal valid full_name ("Jo")
def test_tc_06_update_minimal_valid_full_name(client):
    email = make_email_str("minimalname")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": "Jo"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] == "Jo"

# TC_07 - Update full_name with normal Unicode ("José")
def test_tc_07_update_unicode_full_name(client):
    email = make_email_str("unicodeuser")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": "José"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["full_name"] == "José"


# --------------------------
# Negative Test Cases
# --------------------------
# TC_10 - Update with invalid email format
def test_tc_10_update_invalid_email_format(client):
    email = make_email_str("invalidemail")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"email": "invalid-email-format"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# TC_11 - Update with empty email
def test_tc_11_update_empty_email(client):
    email = make_email_str("emptyemail")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"email": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# TC_12 - Update with empty full_name string
def test_tc_12_update_empty_full_name(client):
    email = make_email_str("emptyfullname")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# TC_13 - Update with whitespace-only full_name
def test_tc_13_update_whitespace_full_name(client):
    email = make_email_str("whitespaceuser")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": "   "})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# TC_14 - Update with invalid role_id (e.g., 99999)
def test_tc_14_update_invalid_role_id(client):
    email = make_email_str("invalidrole")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"role_id": 99999})
    assert response.status_code in (
        status.HTTP_422_UNPROCESSABLE_ENTITY, 
        status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST
    )

# TC_15 - Update user with non-existent user_id
def test_tc_15_update_non_existent_user(client):
    email = make_email_str("nonexistentuser")
    register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)

    response = client.put(f"{ENDPOINT}/99999", headers=token_header, json={"full_name": "Ghost User"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

# TC_16 - Update user with deactivated/deleted account
def test_tc_16_update_deleted_user(client, db_session):
    email = make_email_str("deleteduser")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    # Soft delete or deactivate the user directly via db_session
    user = db_session.query(User).filter(User.id == user_id).first()
    user.is_active = False
    db_session.commit()

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": "Deleted User"})
    assert response.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN, 401)

# TC_17 - Update using wrong data types (e.g., full_name=123)
def test_tc_17_update_wrong_data_type(client):
    email = make_email_str("wrongdatatype")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": 123})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# --------------------------
# Edge Test Cases
# --------------------------

# TC_21 - Update full_name with maximum allowed length (e.g., 100 characters)
def test_tc_21_update_max_full_name_length(client):
    email = make_email_str("maxfullname")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    max_full_name = "A" * 100
    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": max_full_name})
    assert response.status_code == status.HTTP_200_OK

# TC_22 - Update with very minimal valid data (only 1 field)
def test_tc_22_update_minimal_valid_data(client):
    email = make_email_str("minimaldata")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": "Jo"})
    assert response.status_code == status.HTTP_200_OK

# TC_23 - Update with empty JSON {} (no fields sent)
def test_tc_23_update_empty_json(client):
    email = make_email_str("emptyjson")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={})
    assert response.status_code == status.HTTP_200_OK

# TC_24 - Update with additional unknown fields (e.g., nickname)
def test_tc_24_update_with_unknown_fields(client):
    email = make_email_str("unknownfield")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(
        f"{ENDPOINT}/{user_id}",
        headers=token_header,
        json={"nickname": "coolguy"}  # Field not allowed in schema
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# --------------------------
# Corner Test Cases
# --------------------------

def test_tc_31_update_special_characters_full_name(client):
    email = make_email_str("specialchar")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": "@#$%^&*"})
    # If your validation allows, expect 200. Otherwise, expect 422.
    assert response.status_code in (200, 422)

def test_tc_32_update_self_profile(client):
    email = make_email_str("selfupdate")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"full_name": "Updated Name"})
    assert response.status_code == 200

def test_tc_33_update_other_user_as_non_admin(client):
    email1 = make_email_str("user1")
    email2 = make_email_str("user2")

    res1 = register(client, email1, "Password123!", role_id=1)
    register(client, email2, "Password123!", role_id=3)

    res2 = login(client, email1, "Password123!")
    token_header = get_user_token_header(res2)

    # user1 tries to update user2
    response = client.put(f"{ENDPOINT}/{res1.json()['id'] + 1}", headers=token_header, json={"full_name": "Hacker"})
    assert response.status_code == 403

# --------------------------
# Security Test Cases
# --------------------------
def test_tc_40_update_without_auth(client):
    response = client.put(f"{ENDPOINT}/1", json={"full_name": "No Auth"})
    assert response.status_code == 401

def test_tc_41_update_with_expired_token(client):
    email = make_email_str("expiredtoken")
    res1 = register(client, email, "Password123!", role_id=3)
    token = create_test_token(res1.json()["id"], expire_in_minutes=-1)  # expired token
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(f"{ENDPOINT}/{res1.json()['id']}", headers=headers, json={"full_name": "Expired"})
    assert response.status_code == 401

def test_tc_42_update_with_invalid_jwt_signature(client):
    email = make_email_str("invalidsignature")
    res1 = register(client, email, "Password123!", role_id=3)
    token = create_test_token(res1.json()["id"], secret_override="wrongsecret")  # invalid secret
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(f"{ENDPOINT}/{res1.json()['id']}", headers=headers, json={"full_name": "Invalid Sig"})
    assert response.status_code == 401

def test_tc_43_update_admin_field_as_user(client):
    email = make_email_str("rolefail")
    res1 = register(client, email, "Password123!", role_id=1)  # normal user
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"role_id": 1})  # try admin
    assert response.status_code == 403

def test_tc_44_attempt_sql_injection_in_email(client):
    email = make_email_str("sqlinject")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    payload = {"email": "test@example.com'; DROP TABLE users;--"}
    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json=payload)
    assert response.status_code == 422

def test_tc_45_attempt_xss_in_full_name(client):
    email = make_email_str("xssattack")
    res1 = register(client, email, "Password123!", role_id=3)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    payload = {"full_name": "<script>alert(1)</script>"}
    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json=payload)
    # Some backends allow, some reject; depending on your validation
    assert response.status_code in (200, 422)

def test_tc_46_jwt_user_a_update_user_b(client):
    email_a = make_email_str("usera")
    email_b = make_email_str("userb")
    
    register(client, email_a, "Password123!", role_id=1)
    res_b = register(client, email_b, "Password123!", role_id=3)
    res_login_a = login(client, email_a, "Password123!")

    token_header_a = get_user_token_header(res_login_a)

    # User A tries to update User B
    response = client.put(f"{ENDPOINT}/{res_b.json()['id']}", headers=token_header_a, json={"full_name": "Hacked"})
    assert response.status_code == 403

def test_tc_47_cross_user_role_escalation(client):
    email = make_email_str("crossrole")
    res1 = register(client, email, "Password123!", role_id=1)
    res2 = login(client, email, "Password123!")
    token_header = get_user_token_header(res2)
    user_id = res1.json()["id"]

    response = client.put(f"{ENDPOINT}/{user_id}", headers=token_header, json={"role_id": 3})
    assert response.status_code == 403

