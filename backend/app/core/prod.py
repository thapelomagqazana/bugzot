from app.core.base import BaseConfig
from pydantic_settings import SettingsConfigDict

class ProdConfig(BaseConfig):
    """
    Configuration settings for production environment.

    Loads from `.env.prod`.
    """
    model_config = SettingsConfigDict(env_file=".env.prod")
