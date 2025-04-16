from .db.session import SessionLocal
from sqlalchemy.orm import Session
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.jwt import verify_access_token
from app.crud.user import get_user
from app.db.models import User
from app.repositories.user_sql import UserSQLRepository
from app.repositories.user_nosql import UserNoSQLRepository
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin")


def get_db() -> Generator:
    """
    Dependency to get a DB session.
    Closes the session after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_nosql_db():
    """
    Dependency to provide a MongoDB client.
    """
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client.get_database(settings.MONGODB_NAME)
    return db

def get_user_repository(
    db_type: str = Depends(lambda: settings.DB_TYPE), 
    sql_db: Session = Depends(get_db), 
    nosql_db = Depends(get_nosql_db)
):
    """
    Dependency to switch between SQL and NoSQL repositories dynamically.

    - If `DB_TYPE="sql"`, uses `UserSQLRepository`
    - If `DB_TYPE="nosql"`, uses `UserNoSQLRepository`
    """
    if db_type == "nosql":
        return UserNoSQLRepository(nosql_db)
    return UserSQLRepository(sql_db)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo=Depends(get_user_repository)
) -> User:
    """
    Extract the user from the JWT token and load from DB.
    """
    try:
        payload = verify_access_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
