"""Production environment configuration."""

from pydantic_settings import SettingsConfigDict

from app.core.base import BaseConfig


class ProdConfig(BaseConfig):
    """Configuration settings for production environment.

    Loads from `.env.prod`.
    """

    model_config = SettingsConfigDict(env_file=".env.prod")
