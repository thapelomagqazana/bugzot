import pytest
import httpx
from app.db.models import User
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.deps import get_db
from sqlalchemy.orm import Session


BASE_URL = "http://localhost:8000"
SIGNIN_URL = "/auth/signin"
USERS_URL = "/api/users"


@pytest.fixture(scope="module")
def test_client():
    with httpx.Client(base_url=BASE_URL) as client:
        yield client

@pytest.fixture(scope="session", autouse=True)
def clean_database(db: Session):
    """
    Before all tests: clean the database.
    After all tests: clean the database.
    """
    db.query(User).delete()
    db.commit()
    yield
    db.query(User).delete()
    db.commit()


@pytest.fixture(scope="session")
def db():
    yield next(get_db())


@pytest.fixture(scope="function")
def create_test_user(db):
    """
    Create a user for authentication tests.
    """
    def _create_user(name, email, password):
        existing_user = user_crud.get_user_by_email(db, email)
        if existing_user:
            user_crud.delete_user(db, existing_user)
        return user_crud.create_user(db, UserCreate(name=name, email=email, password=password))
    return _create_user


@pytest.fixture(scope="function")
def cleanup_user(db):
    def _cleanup(email):
        user = user_crud.get_user_by_email(db, email)
        if user:
            user_crud.delete_user(db, user)
    return _cleanup


@pytest.fixture(scope="session", autouse=True)
def cleanup_database(db):
    """ Cleanup before and after all tests """
    yield
    users = db.query(user_crud.User).all()
    for user in users:
        user_crud.delete_user(db, user)


# ✅ Positive Test Cases

def test_signin_valid_credentials(test_client, create_test_user, cleanup_user):
    create_test_user("John Doe", "john@example.com", "securepassword")
    payload = {"email": "john@example.com", "password": "securepassword"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()
    cleanup_user("john@example.com")


def test_signin_uppercase_email(test_client, create_test_user, cleanup_user):
    create_test_user("Uppercase", "user@email.com", "securepassword")
    payload = {"email": "USER@EMAIL.COM", "password": "securepassword"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()
    cleanup_user("user@email.com")


def test_signin_after_user_created(test_client, create_test_user, cleanup_user):
    create_test_user("Test User", "newuser@example.com", "securepassword")
    payload = {"email": "newuser@example.com", "password": "securepassword"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()
    cleanup_user("newuser@example.com")



# ❌ Negative Test Cases

def test_signin_wrong_password(test_client, create_test_user, cleanup_user):
    create_test_user("Wrong Password", "wrongpass@example.com", "correctpassword")
    payload = {"email": "wrongpass@example.com", "password": "wrongpassword"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 401
    cleanup_user("wrongpass@example.com")


def test_signin_nonexistent_email(test_client):
    payload = {"email": "nonexistent@example.com", "password": "password"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 401


def test_signin_missing_email(test_client):
    payload = {"password": "password"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 422


def test_signin_missing_password(test_client):
    payload = {"email": "user@example.com"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 422


def test_signin_invalid_email_format(test_client):
    payload = {"email": "invalid-email", "password": "password"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 422


def test_signin_empty_body(test_client):
    response = test_client.post(SIGNIN_URL, json={})
    assert response.status_code == 422


# 🟠 Edge Test Cases

def test_signin_min_password_length(test_client, create_test_user, cleanup_user):
    create_test_user("Min Password", "minpass@example.com", "password")
    payload = {"email": "minpass@example.com", "password": "password"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    cleanup_user("minpass@example.com")


def test_signin_max_password_length(test_client, create_test_user, cleanup_user):
    long_password = "p" * 128
    create_test_user("Max Password", "maxpass@example.com", long_password)
    payload = {"email": "maxpass@example.com", "password": long_password}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    cleanup_user("maxpass@example.com")


def test_signin_max_email_length(test_client, create_test_user, cleanup_user):
    long_email = f"{'a'*64}@{'b'*63}.com"
    create_test_user("Long Email", long_email, "password")
    payload = {"email": long_email, "password": "password"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    cleanup_user(long_email)


def test_signin_min_email_length(test_client, create_test_user, cleanup_user):
    create_test_user("Min Email", "a@b.co", "password")
    payload = {"email": "a@b.co", "password": "password"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    cleanup_user("a@b.co")


# 🟡 Corner Test Cases
def test_signin_email_mixed_cases_spaces(test_client, create_test_user, cleanup_user):
    create_test_user("Mixed Email", "user@email.com", "password")
    payload = {"email": "  User@Email.Com  ", "password": "password"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    cleanup_user("user@email.com")


def test_signin_special_char_password(test_client, create_test_user, cleanup_user):
    create_test_user("Special Pass", "special@example.com", "@dm1n!@#")
    payload = {"email": "special@example.com", "password": "@dm1n!@#"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code == 200
    cleanup_user("special@example.com")


def test_signin_unicode_email(test_client, create_test_user, cleanup_user):
    create_test_user("Unicode User", "测试@example.com", "password")
    payload = {"email": "测试@example.com", "password": "password"}
    response = test_client.post(SIGNIN_URL, json=payload)
    assert response.status_code in [200, 422]
    cleanup_user("测试@example.com")


def test_signin_inactive_user(test_client):
    # Requires implementation of active/inactive status.
    pass
