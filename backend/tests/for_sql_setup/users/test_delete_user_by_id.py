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
    def _create(name, email, password, role="user"):
        existing_user = user_crud.get_user_by_email(db, email)
        if existing_user:
            user_crud.delete_user(db, existing_user)
        return user_crud.create_user(db, UserCreate(name=name, email=email, password=password, role=role))
    return _create


@pytest.fixture(scope="function")
def signin(test_client, create_user):
    def _signin(email, password, role="user"):
        user = create_user("Auth User", email, password, role)
        response = test_client.post(SIGNIN_URL, json={"email": email, "password": password})
        token = response.json()["access_token"]
        return token, user.id
    return _signin


@pytest.fixture(scope="function")
def cleanup_user(db):
    def _cleanup(email):
        user = user_crud.get_user_by_email(db, email)
        if user:
            user_crud.delete_user(db, user)
    return _cleanup


# Positive Test Cases

def test_delete_existing_user(test_client, create_user, signin):
    user = create_user("Delete User", "delete@example.com", "password")
    token, _ = signin("admin@example.com", "password", "admin")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/{user.id}", headers=headers)
    assert response.status_code == 204


def test_delete_own_profile(test_client, signin):
    token, user_id = signin("own@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/{user_id}", headers=headers)
    assert response.status_code == 204


# Negative Test Cases

def test_delete_nonexistent_user(test_client, signin):
    token, _ = signin("nonexistent@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/9999", headers=headers)
    assert response.status_code == 404


def test_delete_user_negative_id(test_client, signin):
    token, _ = signin("negative@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/-1", headers=headers)
    assert response.status_code == 404


def test_delete_user_invalid_id_string(test_client, signin):
    token, _ = signin("stringid@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/abc", headers=headers)
    assert response.status_code == 422


def test_delete_user_unauthorized(test_client):
    response = test_client.delete(f"{USERS_URL}/1")
    assert response.status_code == 401


def test_delete_forbidden_user(test_client, create_user, signin):
    victim = create_user("Victim", "victim@example.com", "password")
    token, _ = signin("attacker@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/{victim.id}", headers=headers)
    assert response.status_code == 403


# Edge Test Cases

def test_delete_max_integer_user_id(test_client, signin):
    token, _ = signin("maxint@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/2147483647", headers=headers)
    assert response.status_code == 404

# Corner Test Cases

def test_delete_user_special_chars_id(test_client, signin):
    token, _ = signin("specialchars@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/%24%23%40", headers=headers)
    assert response.status_code == 422


def test_delete_deleted_user(test_client, create_user, signin, db):
    deleted_user = create_user("Deleted User", "deleted@example.com", "password")
    db.delete(deleted_user)
    db.commit()
    token, _ = signin("requester@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/{deleted_user.id}", headers=headers)
    assert response.status_code == 404

def test_delete_user_id_with_spaces(test_client, signin):
    token, _ = signin("spaces@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.delete(f"{USERS_URL}/%20%201%20%20", headers=headers)
    assert response.status_code == 404
