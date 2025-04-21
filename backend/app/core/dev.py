from app.core.base import BaseConfig
from pydantic_settings import SettingsConfigDict

class DevConfig(BaseConfig):
    """
    Configuration settings for development environment.

    Loads from `.env.dev`.
    """
    model_config = SettingsConfigDict(env_file=".env.dev")