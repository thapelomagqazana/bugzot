import pytest
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from app.main import app
from tests.utils import register, make_email_str

client = TestClient(app)

# -----------------------
# ✅ Positive Test Cases
# -----------------------
def test_tc_01_register_valid_user(client: TestClient):
    res = register(client, make_email_str("user1"), "StrongPass123!", "John Doe")
    assert res.status_code == HTTP_201_CREATED
    assert res.json()["email"] == "user1@protonmail.com"


def test_tc_02_register_email_with_whitespace_and_uppercase(client: TestClient):
    res = register(client, "  USER@Protonmail.Com  ", "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED
    assert res.json()["email"] == "user@protonmail.com"  # normalized


def test_tc_03_register_with_optional_full_name(client: TestClient):
    res = register(client, make_email_str("namedemail"), "StrongPass123!", "Named User")
    assert res.status_code == HTTP_201_CREATED
    assert res.json()["full_name"] == "Named User"


def test_tc_04_register_without_full_name(client: TestClient):
    res = register(client, make_email_str("noname"), "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED
    assert res.json().get("full_name") in (None, "")


def test_tc_05_re_register_after_failed_previous(client: TestClient):
    email = make_email_str("retest")
    register(client, email, "StrongPass123!")
    res = register(client, email, "StrongPass123!")  # should trigger 409 Conflict or resend logic
    assert res.status_code in (HTTP_409_CONFLICT, HTTP_201_CREATED)


def test_tc_06_register_with_valid_non_disposable_domain(client: TestClient):
    res = register(client, "domaincheck@protonmail.com", "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED


# -----------------------
# ❌ Negative Test Cases
# -----------------------

def test_tc_10_missing_email(client: TestClient):
    res = client.post("/api/v1/auth/register", json={"password": "StrongPass123!"})
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_11_missing_password(client: TestClient):
    res = client.post("/api/v1/auth/register", json={"email": "missingpass@example.com"})
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_12_weak_password(client: TestClient):
    res = register(client, "weakpass@example.com", "123")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_13_duplicate_email(client: TestClient):
    email = make_email_str("duplicate")
    register(client, email, "StrongPass123!")
    res = register(client, email, "StrongPass123!")
    assert res.status_code == HTTP_409_CONFLICT


def test_tc_14_invalid_email_format(client: TestClient):
    res = register(client, "invalid-email", "StrongPass123!")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_15_email_no_mx(client: TestClient):
    res = register(client, "nxdomain@invalidtld.test", "StrongPass123!")
    assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


def test_tc_16_disposable_email(client: TestClient):
    res = register(client, "temp@tempmail.com", "StrongPass123!")
    assert res.status_code == HTTP_400_BAD_REQUEST


def test_tc_17_honeypot_trigger(client: TestClient):
    headers = {"honeypot": "gotcha"}  # Simulate bot behavior
    res = client.post("/api/v1/auth/register", json={"email": "bot@caught.com", "password": "StrongPass123!"}, headers=headers)
    assert res.status_code == HTTP_400_BAD_REQUEST
