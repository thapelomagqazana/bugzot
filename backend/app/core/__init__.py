"""Core configuration package for environment-specific settings."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings

@lru_cache
def get_settings() -> BaseSettings:
    """Load settings for the current environment (cached).

    Automatically determines the current environment and loads the appropriate
    configuration class. Defaults to development if ENVIRONMENT is not explicitly set.

    Returns:
        BaseSettings: Instance with all config fields loaded from the correct .env file.

    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        from app.core.prod import ProdConfig
        return ProdConfig()

    if env == "staging":
        from app.core.staging import StagingConfig
        return StagingConfig()

    from app.core.dev import DevConfig
    return DevConfig()
