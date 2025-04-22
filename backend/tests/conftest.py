import pytest
from sqlalchemy import text
from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.db import TestingSessionLocal, test_engine
from fastapi.testclient import TestClient
from app.db.init_db import seed_roles


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    print(f"\n🔍 Using TEST DB URL: {test_engine.url}\n")
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Seed roles ONCE
    db = TestingSessionLocal()
    try:
        seed_roles(db)
        db.commit()
    finally:
        db.close()

    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Fresh DB session for each test. Auto-cleans via transaction rollback.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()  # rollback all test-created data
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
