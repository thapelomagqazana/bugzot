"""Defines shared base settings for all environments using Pydantic."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Base settings shared across environments.

    Inherits from Pydantic's BaseSettings to support environment variable loading.
    Defines all core variables used across development, staging, and production.
    """

    # Application metadata
    PROJECT_NAME: str
    ENVIRONMENT: str
    DEBUG: bool
    API_VERSION: str

    # PostgreSQL database connection
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    DATABASE_URL: str  # Full connection string (sync/async support)

    # Redis cache connection
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # CORS config
    BACKEND_CORS_ORIGINS: str

    # JWT authentication config
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Tells Pydantic to treat values as case-sensitive
    # and load from UTF-8 encoded `.env` files
    model_config = SettingsConfigDict(env_file_encoding="utf-8")
