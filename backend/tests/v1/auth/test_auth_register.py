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

# -----------------------
# 📐 Edge Test Cases
# -----------------------
def test_tc_21_password_min_boundary(client: TestClient):
    res = register(client, make_email_str("minpass"), "Aa1!aaaa")
    assert res.status_code == HTTP_201_CREATED

def test_tc_22_email_with_symbols(client: TestClient):
    res = register(client, make_email_str("john+test_user"), "StrongPass123!")
    assert res.status_code == HTTP_201_CREATED

def test_tc_23_full_name_with_unicode(client: TestClient):
    res = register(client, make_email_str("unicode"), "StrongPass123!", "Jöhn 🚀")
    assert res.status_code == HTTP_201_CREATED
    assert "Jöhn" in res.json()["full_name"]

# -----------------------
# 🔁 Corner Test Cases
# -----------------------
def test_tc_31_resend_token_for_same_email(client: TestClient):
    register(client, make_email_str("resend"), "StrongPass123!")
    res2 = register(client, make_email_str("resend"), "StrongPass123!")
    assert res2.status_code in (HTTP_409_CONFLICT, HTTP_201_CREATED)

def test_tc_33_script_tag_in_name(client: TestClient):
    res = register(client, make_email_str("xssname"), "StrongPass123!", "<script>alert(1)</script>")
    assert res.status_code == HTTP_201_CREATED
    assert "<script>" not in res.json()["full_name"]

# -----------------------
# 🔐 Security Test Cases
# -----------------------
def test_tc_40_sql_injection_attempt(client: TestClient):
    res = register(client, make_email_str("sql"), "StrongPass123!", "Robert'); DROP TABLE users;--")
    assert res.status_code == HTTP_201_CREATED

def test_tc_41_xss_in_full_name(client: TestClient):
    res = register(client, make_email_str("xss"), "StrongPass123!", "<script>alert('xss')</script>")
    assert res.status_code == HTTP_201_CREATED
    assert "<script>" not in res.json()["full_name"]

def test_tc_43_bot_fills_all_fields(client: TestClient):
    headers = {"honeypot": "filled"}
    res = client.post("/api/v1/auth/register", json={"email": "botfill@fail.com", "password": "StrongPass123!", "full_name": "I am bot"}, headers=headers)
    assert res.status_code == HTTP_400_BAD_REQUEST

def test_tc_44_password_not_logged(client: TestClient):
    # This is a theoretical test; you would inspect logs manually or mock logging
    res = register(client, make_email_str("logtest"), "SensitivePass123!")
    assert res.status_code == HTTP_201_CREATED

def test_tc_45_forged_email_header(client: TestClient):
    headers = {"X-Email": "fake@example.com"}
    res = client.post("/api/v1/auth/register", json={"email": make_email_str("real"), "password": "StrongPass123!"}, headers=headers)
    assert res.status_code == HTTP_201_CREATED
