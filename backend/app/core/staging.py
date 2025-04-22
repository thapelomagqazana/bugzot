"""Staging environment-specific configuration and overrides."""

from pydantic_settings import SettingsConfigDict

from app.core.base import BaseConfig


class StagingConfig(BaseConfig):
    """Configuration settings for staging environment.

    Loads from `.env.staging`.
    """

    model_config = SettingsConfigDict(env_file=".env.staging")
