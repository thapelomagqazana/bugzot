from functools import lru_cache
import os
from app.core.dev import DevConfig
from app.core.staging import StagingConfig
from app.core.prod import ProdConfig

@lru_cache()
def get_settings():
    """
    Cached settings loader for current environment.

    Automatically determines the current environment and loads the appropriate configuration class.
    Defaults to development if ENVIRONMENT is not explicitly set.
    Returns:
        BaseConfig instance with all config fields loaded from relevant .env file.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        return ProdConfig()
    elif env == "staging":
        return StagingConfig()
    return DevConfig()
