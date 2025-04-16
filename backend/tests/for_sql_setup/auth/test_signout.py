import pytest
import httpx
from app.db.models import User
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.deps import get_db
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from app.utils.jwt import create_access_token

BASE_URL = "http://localhost:8000"
SIGNIN_URL = "/auth/signin"
SIGNOUT_URL = "/auth/signout"

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
        user = create_user("Test User", email, password)
        response = test_client.post(SIGNIN_URL, json={"email": email, "password": password})
        token = response.json()["access_token"]
        return token, user.id
    return _signin

# ✅ Positive Test Cases

def test_signout_valid_user(test_client, signin):
    token, _ = signin("validuser@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code == 200

def test_multiple_signouts(test_client, signin):
    token, _ = signin("multisignout@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(3):
        response = test_client.post(SIGNOUT_URL, headers=headers)
        assert response.status_code == 200

def test_signout_after_signin(test_client, signin):
    token, _ = signin("freshsignin@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code == 200

def test_signout_special_chars_email(test_client, signin):
    token, _ = signin("special!user@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code == 200

# ❌ Negative Test Cases

@pytest.mark.parametrize("token", ["invalidtoken", "Bearer invalid", None])
def test_signout_invalid_or_missing_token(test_client, token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code == 401

def test_signout_expired_token(test_client):
    expired_token = create_access_token(
        {"user_id": 1},
        expires_delta=timedelta(seconds=-1)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code == 401

def test_signout_tampered_token(test_client):
    tampered_token = "tampered.jwt.token"
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code == 401

# 🟠 Edge Test Cases

def test_signout_after_deletion(test_client, create_user, db):
    user = create_user("Deleted User", "deleted@example.com", "password123")
    token = create_access_token({"user_id": user.id})
    db.delete(user)
    db.commit()
    headers = {"Authorization": f"Bearer {token}"}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code in [401, 404]

def test_signout_large_token(test_client):
    large_token = "A" * 10000
    headers = {"Authorization": f"Bearer {large_token}"}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code == 401

# 🟡 Corner Test Cases

def test_signout_special_chars_token(test_client):
    headers = {"Authorization": "Bearer #$%^&*()!"}
    response = test_client.post(SIGNOUT_URL, headers=headers)
    assert response.status_code == 401

def test_signout_during_heavy_load(test_client, signin):
    token, _ = signin("loadtest@example.com", "password123")
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(1000):
        response = test_client.post(SIGNOUT_URL, headers=headers)
        assert response.status_code == 200
