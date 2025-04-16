import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """

    # Database Settings
    DB_TYPE: str = os.getenv("DB_TYPE", "sql")
    SQL_URL: str = os.getenv("SQL_URL", "postgresql+psycopg2://skeleton_user:skeleton_pass@localhost:5432/skeleton_db")
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_NAME: str = os.getenv("MONGODB_NAME", "fastapi_db")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # CORS Configuration
    BACKEND_CORS_ORIGINS: str = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173")

    class Config:
        env_file = ".env"  # Allows loading environment variables from a `.env` file

# Create a settings instance
settings = Settings()
