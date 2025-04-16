import pytest
import httpx
from sqlalchemy.orm import Session
from app.deps import get_db
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.db.models import User

BASE_URL = "http://localhost:8000/api/users"


@pytest.fixture(scope="session")
def db() -> Session:
    """
    Provide a single DB session for the whole test session.
    """
    yield next(get_db())


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


@pytest.fixture(scope="module")
def test_client():
    """
    HTTP client for tests.
    """
    with httpx.Client(base_url=BASE_URL) as client:
        yield client


@pytest.fixture(scope="function")
def cleanup_user(db: Session):
    """
    Cleanup any user with the given email after test.
    """
    def _cleanup(email: str):
        user = user_crud.get_user_by_email(db, email)
        if user:
            user_crud.delete_user(db, user)
    return _cleanup


# Positive Test Cases

def test_create_valid_user(test_client, cleanup_user):
    payload = {"name": "John Doe", "email": "john@example.com", "password": "securepassword"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "john@example.com"
    assert data["name"] == "John Doe"
    assert "id" in data
    cleanup_user("john@example.com")


def test_create_user_max_name_length(test_client, cleanup_user):
    name = "a" * 255
    payload = {"name": name, "email": "maxname@example.com", "password": "securepassword"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == name
    assert data["email"] == "maxname@example.com"
    cleanup_user("maxname@example.com")


def test_create_user_special_chars_in_name(test_client, cleanup_user):
    payload = {"name": "John_Doe!", "email": "special@example.com", "password": "securepassword"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John_Doe!"
    assert data["email"] == "special@example.com"
    cleanup_user("special@example.com")


# Negative Test Cases

def test_create_user_duplicate_email(test_client, db):
    user_crud.create_user(db, UserCreate(name="Duplicate", email="dup@example.com", password="password"))
    payload = {"name": "Duplicate2", "email": "dup@example.com", "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Email already registered."
    user = user_crud.get_user_by_email(db, "dup@example.com")
    if user:
        user_crud.delete_user(db, user)


def test_create_user_missing_name(test_client):
    payload = {"email": "noname@example.com", "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_user_invalid_email(test_client):
    payload = {"name": "InvalidEmail", "email": "invalid-email", "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_user_short_password(test_client):
    payload = {"name": "ShortPass", "email": "shortpass@example.com", "password": "pw"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_user_empty_body(test_client):
    response = test_client.post("/", json={})
    assert response.status_code == 422
    assert "detail" in response.json()


# Edge Test Cases

def test_create_user_edge_max_name_length(test_client, cleanup_user):
    name = "a" * 255
    payload = {"name": name, "email": "edge_max_name@example.com", "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == name
    assert data["email"] == "edge_max_name@example.com"
    cleanup_user("edge_max_name@example.com")


def test_create_user_edge_max_email_length(test_client, cleanup_user):
    long_email = f"{'a'*64}@{'b'*63}.com"
    payload = {"name": "EdgeEmail", "email": long_email, "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == long_email
    assert data["name"] == "EdgeEmail"
    cleanup_user(long_email)


def test_create_user_edge_min_password_length(test_client, cleanup_user):
    payload = {"name": "MinPass", "email": "minpass@example.com", "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "minpass@example.com"
    assert data["name"] == "MinPass"
    cleanup_user("minpass@example.com")


def test_create_user_edge_max_password_length(test_client, cleanup_user):
    payload = {"name": "MaxPass", "email": "maxpass@example.com", "password": "p" * 128}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "maxpass@example.com"
    assert data["name"] == "MaxPass"
    cleanup_user("maxpass@example.com")


# Corner Test Cases

def test_create_user_name_only_spaces(test_client):
    payload = {"name": " ", "email": "spaces@example.com", "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_user_uppercase_email(test_client, cleanup_user):
    payload = {"name": "UpperCaseEmail", "email": "USER@EMAIL.COM", "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "USER@EMAIL.COM".lower()
    assert data["name"] == "UpperCaseEmail"
    cleanup_user("USER@EMAIL.COM")


def test_create_user_password_only_spaces(test_client):
    payload = {"name": "SpacesPass", "email": "spacespass@example.com", "password": " "}
    response = test_client.post("/", json=payload)
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_user_unicode_name(test_client, cleanup_user):
    payload = {"name": "测试用户", "email": "unicode@example.com", "password": "password"}
    response = test_client.post("/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "unicode@example.com"
    assert data["name"] == "测试用户"
    cleanup_user("unicode@example.com")
