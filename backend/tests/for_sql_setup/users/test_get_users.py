import pytest
import httpx
from app.db.models import User
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.deps import get_db
from sqlalchemy.orm import Session

BASE_URL = "http://localhost:8000"
USERS_URL = "/api/users/"


@pytest.fixture(scope="session")
def db():
    yield next(get_db())


@pytest.fixture(scope="session", autouse=True)
def clean_database(db: Session):
    """ BeforeAll and AfterAll: Clean database """
    db.query(User).delete()
    db.commit()
    yield
    db.query(User).delete()
    db.commit()


@pytest.fixture(scope="function")
def create_test_user(db):
    """ Create a user """
    def _create_user(name, email, password):
        existing_user = user_crud.get_user_by_email(db, email)
        if existing_user:
            user_crud.delete_user(db, existing_user)
        return user_crud.create_user(db, UserCreate(name=name, email=email, password=password))
    return _create_user


@pytest.fixture(scope="function")
def cleanup_users(db):
    """ Cleanup all users after test """
    def _cleanup():
        db.query(User).delete()
        db.commit()
    return _cleanup


@pytest.fixture(scope="module")
def test_client():
    with httpx.Client(base_url=BASE_URL) as client:
        yield client


# Positive Test Cases

def test_get_all_users(test_client, create_test_user, cleanup_users):
    create_test_user("User One", "one@example.com", "password")
    create_test_user("User Two", "two@example.com", "password")
    response = test_client.get(USERS_URL)
    assert response.status_code == 200
    assert len(response.json()) == 2
    cleanup_users()


def test_get_users_with_pagination(test_client, create_test_user, cleanup_users):
    for i in range(10):
        create_test_user(f"User {i}", f"user{i}@example.com", "password")
    response = test_client.get(f"{USERS_URL}?skip=0&limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5
    cleanup_users()


def test_get_users_when_no_users_exist(test_client, cleanup_users):
    cleanup_users()
    response = test_client.get(USERS_URL)
    assert response.status_code == 200
    assert response.json() == []


# Negative Test Cases

def test_get_users_invalid_skip(test_client):
    response = test_client.get(f"{USERS_URL}?skip=-1")
    assert response.status_code == 422


def test_get_users_invalid_limit(test_client):
    response = test_client.get(f"{USERS_URL}?limit=-10")
    assert response.status_code == 422


def test_get_users_exceedingly_large_limit(test_client):
    response = test_client.get(f"{USERS_URL}?limit=10000")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# def test_get_users_unauthorized_access():
#     # Example: If auth is required, this test should use an invalid or missing token
#     headers = {"Authorization": "Bearer invalid_token"}
#     with httpx.Client(base_url=BASE_URL, headers=headers) as client:
#         response = client.get(USERS_URL)
#         assert response.status_code == 401


# Edge Test Cases

def test_get_users_zero_users(test_client, cleanup_users):
    cleanup_users()
    response = test_client.get(USERS_URL)
    assert response.status_code == 200
    assert response.json() == []


def test_get_users_max_integer_skip(test_client):
    response = test_client.get(f"{USERS_URL}?skip=2147483647")
    assert response.status_code == 200
    assert response.json() == []


def test_get_users_max_integer_limit(test_client):
    response = test_client.get(f"{USERS_URL}?limit=2147483647")
    assert response.status_code == 422


def test_get_users_exactly_one_user(test_client, create_test_user, cleanup_users):
    cleanup_users()
    create_test_user("Single User", "single@example.com", "password")
    response = test_client.get(USERS_URL)
    assert response.status_code == 200
    assert len(response.json()) == 1
    cleanup_users()


# Corner Test Cases

def test_get_users_skip_larger_than_total(test_client, create_test_user, cleanup_users):
    for i in range(10):
        create_test_user(f"User {i}", f"user{i}@example.com", "password")
    response = test_client.get(f"{USERS_URL}?skip=1000")
    assert response.status_code == 200
    assert response.json() == []
    cleanup_users()


def test_get_users_limit_larger_than_total(test_client, create_test_user, cleanup_users):
    for i in range(10):
        create_test_user(f"User {i}", f"user{i}@example.com", "password")
    response = test_client.get(f"{USERS_URL}?limit=1000")
    assert response.status_code == 200
    assert len(response.json()) == 10
    cleanup_users()


def test_get_users_special_characters_in_params(test_client):
    response = test_client.get(f"{USERS_URL}?skip=abc&limit=xyz")
    assert response.status_code == 422


def test_get_users_high_skip_small_limit(test_client, create_test_user, cleanup_users):
    for i in range(10):
        create_test_user(f"User {i}", f"user{i}@example.com", "password")
    response = test_client.get(f"{USERS_URL}?skip=1000&limit=5")
    assert response.status_code == 200
    assert response.json() == []
    cleanup_users()
