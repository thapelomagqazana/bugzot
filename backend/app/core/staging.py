from app.core.base import BaseConfig
from pydantic_settings import SettingsConfigDict

class StagingConfig(BaseConfig):
    """
    Configuration settings for staging environment.

    Loads from `.env.staging`.
    """
    model_config = SettingsConfigDict(env_file=".env.staging")
