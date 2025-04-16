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

@pytest.fixture(scope="function")
def signin(test_client, create_user):
    def _signin(email, password):
        user = create_user("Auth User", email, password)
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

def test_get_existing_user_by_valid_user_id(test_client, create_user):
    user = create_user("Valid User", "valid@example.com", "password")
    
    # Sign in the same user you created
    response = test_client.post(SIGNIN_URL, json={"email": "valid@example.com", "password": "password"})
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/{user.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == user.id



def test_get_user_with_max_user_id(test_client, db, signin):
    max_id = db.query(User).order_by(User.id.desc()).first().id
    token, _ = signin("maxid@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/{max_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == max_id


def test_get_own_profile(test_client, signin):
    token, user_id = signin("ownprofile@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == user_id


# ❌ Negative Test Cases

def test_get_nonexistent_user(test_client, signin):
    token, _ = signin("nonexistent@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/9999", headers=headers)
    assert response.status_code == 404


def test_get_user_negative_id(test_client, signin):
    token, _ = signin("negativeid@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/-1", headers=headers)
    assert response.status_code == 422


def test_get_user_invalid_id_string(test_client, signin):
    token, _ = signin("stringid@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/abc", headers=headers)
    assert response.status_code == 422


def test_get_user_unauthorized(test_client):
    response = test_client.get(f"{USERS_URL}/1")
    assert response.status_code == 401


# 🟠 Edge Test Cases

def test_get_user_id_zero(test_client, signin):
    token, _ = signin("zeroid@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/0", headers=headers)
    assert response.status_code == 422


def test_get_user_large_id(test_client, signin):
    token, _ = signin("largeid@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/2147483647", headers=headers)
    assert response.status_code == 404


def test_get_first_user(test_client, create_user, signin):
    user = create_user("First User", "first@example.com", "password")
    token, _ = signin("firstuser@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/{user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == user.id

def test_get_user_just_beyond_last_id(test_client, create_user, signin, db):
    create_user("Last User", "last@example.com", "password")
    last_user_id = db.query(User).order_by(User.id.desc()).first().id
    token, _ = signin("beyondlast@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/{last_user_id + 2}", headers=headers)
    assert response.status_code == 404

# 🟡 Corner Test Cases

def test_get_user_special_chars(test_client, signin):
    token, _ = signin("specialchars@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/%24%23%40", headers=headers)
    assert response.status_code == 422


def test_get_deleted_user(test_client, create_user, signin, db):
    deleted_user = create_user("Deleted User", "deleted@example.com", "password")
    db.delete(deleted_user)
    db.commit()
    token, _ = signin("requester@example.com", "password")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.get(f"{USERS_URL}/{deleted_user.id}", headers=headers)
    assert response.status_code == 404
