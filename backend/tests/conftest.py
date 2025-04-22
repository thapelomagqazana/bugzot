"""Pytest fixtures for setting up and tearing down the test database and client."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import TestingSessionLocal, test_engine
from app.db.base import Base
from app.db.init_db import seed_roles
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> None:
    """Initialize the test database and seed roles once per session."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        seed_roles(db)
        db.commit()
    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Session:
    """Return a fresh DB session per test using transaction rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Return a FastAPI test client with DB dependency overridden."""

    def override_get_db() -> Session:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
