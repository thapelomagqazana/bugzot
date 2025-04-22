import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.utils import get_user_from_db, register

client = TestClient(app)

# -----------------------
# ✅ Positive Test Cases
# -----------------------

def test_tc_01_register_valid_user(client):
    res = register(client, "user1@example.com", "StrongPass123!", "Alice")
    assert res.status_code == 201
    assert res.json()["email"] == "user1@example.com"


def test_tc_02_register_no_full_name(client):
    res = register(client, "user2@example.com", "StrongPass123!")
    assert res.status_code == 201
    assert res.json().get("full_name") in (None, "")

def test_tc_03_email_lowercase(client):
    res = register(client, "User3@Example.COM", "StrongPass123!")
    assert res.status_code == 201
    assert res.json()["email"] == "user3@example.com"

def test_tc_04_default_role(client):
    res = register(client, "user4@example.com", "StrongPass123!")
    assert res.status_code == 201
    assert res.json()["role_id"] == 1  # Adjust if needed

# ------------------------
# ❌ Negative Test Cases
# ------------------------

def test_tc_05_duplicate_email(client):
    register(client, "user5@example.com", "StrongPass123!")
    res = register(client, "user5@example.com", "AnotherPass!")
    assert res.status_code == 409
    assert "already registered" in res.json()["detail"]

def test_tc_06_empty_email():
    res = register(client, "", "StrongPass123!")
    assert res.status_code == 422

def test_tc_07_empty_password():
    res = register(client, "user7@example.com", "")
    assert res.status_code == 422

def test_tc_08_short_password():
    res = register(client, "user8@example.com", "123")
    assert res.status_code == 422

def test_tc_09_invalid_email_format():
    res = register(client, "invalid-email", "StrongPass123!")
    assert res.status_code == 422

def test_tc_10_long_full_name():
    long_name = "A" * 600
    res = register(client, "user10@example.com", "StrongPass123!", long_name)
    assert res.status_code in [400, 422]

# ---------------------
# 🌐 EDGE TEST CASES
# ---------------------

def test_tc_11_email_mixed_case(client, db_session):
    res = register(client, "TestUser@Example.COM", "StrongPass123!")
    assert res.status_code == 201
    user = get_user_from_db(db_session, "testuser@example.com")  # normalized
    assert user.email == "testuser@example.com"

def test_tc_12_password_special_chars_only(client):
    res = register(client, "specialchar@example.com", "!@#$%^&*()")
    assert res.status_code == 201

def test_tc_13_empty_full_name(client):
    res = register(client, "emptyname@example.com", "StrongPass123!", "")
    assert res.status_code == 201
    assert res.json()["full_name"] in [None, ""]

def test_tc_14_email_with_spaces(client, db_session):
    res = register(client, "  user.space@example.com  ", "StrongPass123!")
    assert res.status_code == 201
    user = get_user_from_db(db_session, "user.space@example.com")
    assert user is not None

# ---------------------
# 🔲 CORNER TEST CASES
# ---------------------
@pytest.mark.skip(reason="Race condition requires transaction-safe locking or retry logic")
def test_tc_15_race_condition_same_email(client):
    from concurrent.futures import ThreadPoolExecutor

    def attempt_register():
        return register(client, "race@example.com", "StrongPass123!")

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: attempt_register(), range(2)))

    statuses = [res.status_code for res in results]
    assert 201 in statuses and 409 in statuses

def test_tc_16_large_full_name(client):
    long_name = "X" * 2_000_000
    res = register(client, "huge@example.com", "StrongPass123!", long_name)
    assert res.status_code in [413, 422, 400]

@pytest.mark.skip(reason="Reserved email check not implemented yet")
def test_tc_17_reserved_admin_email(client):
    res = register(client, "admin@example.com", "StrongPass123!")
    assert res.status_code in [403, 422]