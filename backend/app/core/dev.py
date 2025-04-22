"""Development environment-specific configuration and overrides."""

from pydantic_settings import SettingsConfigDict

from app.core.base import BaseConfig


class DevConfig(BaseConfig):
    """Configuration settings for development environment.

    Loads from `.env.dev`.
    """

    model_config = SettingsConfigDict(env_file=".env.dev")
