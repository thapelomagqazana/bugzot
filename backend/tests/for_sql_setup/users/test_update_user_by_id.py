import pytest
import httpx
from app.db.models import User
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.deps import get_db
from sqlalchemy.orm import Session

BASE_URL = "http://localhost:8000"
USERS_URL = "/api/users"
SIGNIN_URL = "/auth/signin"

@pytest.fixture(scope="session")
def db():
    yield next(get_db())

@pytest.fixture(scope="module")
def test_client():
    with httpx.Client(base_url=BASE_URL) as client:
        yield client

@pytest.fixture(scope="function")
def create_user(db):
    def _create(name, email, password):
        existing_user = user_crud.get_user_by_email(db, email)
        if existing_user:
            user_crud.delete_user(db, existing_user)
        return user_crud.create_user(db, UserCreate(name=name, email=email, password=password))
    return _create

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

@pytest.fixture(scope="function")
def cleanup_user(db):
    def _cleanup(email):
        user = user_crud.get_user_by_email(db, email)
        if user:
            user_crud.delete_user(db, user)
    return _cleanup

@pytest.fixture(scope="function")
def signin(test_client, create_user):
    def _signin(email, password):
        user = create_user("Test User", email, password)
        response = test_client.post(SIGNIN_URL, json={"email": email, "password": password})
        return response.json()["access_token"], user.id
    return _signin


# Positive Test Cases

def test_update_user_name(test_client, signin, cleanup_user):
    email = "update_name@example.com"
    token, user_id = signin(email, "password")
    payload = {"name": "New Name"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/{user_id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    cleanup_user(email)


def test_update_user_email(test_client, signin, cleanup_user):
    email = "update_email@example.com"
    token, user_id = signin(email, "password")
    payload = {"email": "newemail@example.com"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/{user_id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "newemail@example.com"
    cleanup_user(email)


def test_update_user_password(test_client, signin, cleanup_user):
    email = "update_password@example.com"
    token, user_id = signin(email, "password")
    payload = {"password": "newpass123"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/{user_id}", json=payload, headers=headers)
    assert response.status_code == 200
    cleanup_user(email)


def test_partial_update_user(test_client, signin, cleanup_user):
    email = "partial_update@example.com"
    token, user_id = signin(email, "password")
    payload = {"name": "Updated Name"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/{user_id}", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"
    cleanup_user(email)


# Negative Test Cases

def test_update_nonexistent_user(test_client, signin):
    token, _ = signin("nonexistent_user@example.com", "password")
    payload = {"name": "Should Fail"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/9999", json=payload, headers=headers)
    assert response.status_code == 404


def test_update_user_invalid_id_string(test_client, signin):
    token, _ = signin("invalid_id_string@example.com", "password")
    payload = {"name": "Invalid ID"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/abc", json=payload, headers=headers)
    assert response.status_code == 422


def test_update_user_unauthorized(test_client):
    payload = {"name": "Unauthorized"}
    response = test_client.put(f"{USERS_URL}/1", json=payload)
    assert response.status_code == 401


# Edge Test Cases

def test_update_user_long_name(test_client, signin):
    token, user_id = signin("long_name@example.com", "password")
    payload = {"name": "A" * 255}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/{user_id}", json=payload, headers=headers)
    assert response.status_code in [200, 422]


def test_update_max_integer_user_id(test_client, signin):
    token, _ = signin("max_int@example.com", "password")
    payload = {"name": "Max Int"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/2147483647", json=payload, headers=headers)
    assert response.status_code == 404


# Corner Test Cases

def test_update_user_special_chars_in_name(test_client, signin):
    token, user_id = signin("special_chars@example.com", "password")
    payload = {"name": "!@#$%^&*()"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/{user_id}", json=payload, headers=headers)
    assert response.status_code in [200, 422]


def test_update_user_with_extra_fields(test_client, signin):
    token, user_id = signin("extra_fields@example.com", "password")
    payload = {"name": "John", "extra": "ignored"}
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.put(f"{USERS_URL}/{user_id}", json=payload, headers=headers)
    assert response.status_code == 200
