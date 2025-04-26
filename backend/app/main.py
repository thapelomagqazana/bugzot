"""FastAPI application entry point and environment configuration checker."""

from fastapi import FastAPI
from app.api.v1.routes import auth, users
from app.core.logging_config import setup_logging
from app.middleware.logging_middleware import LoggingContextMiddleware
from app.core import get_settings
from app.db import engine
import logging

# Load the configuration once
settings = get_settings()
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)
app.add_middleware(LoggingContextMiddleware)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/")
def health_check() -> dict:
    """Return health check status."""
    return {
        "status": "ok",
        "message": "BugZot API is up!",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


@app.on_event("startup")
def log_db_info() -> None:
    """
    Log database connection info at startup using structured logs.
    """
    logger = logging.getLogger("startup")
    logger.info("🚀 Connected to database", extra={"db_url": str(engine.url)})
