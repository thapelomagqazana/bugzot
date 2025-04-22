"""FastAPI application entry point and environment configuration checker."""

from fastapi import FastAPI

from app.api.v1.routes import auth
from app.core import get_settings
from app.db import engine

# Load the configuration once
settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)

app.include_router(auth.router, prefix="/api/v1")

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
    """Log database connection info at startup."""
    # Use logging instead of print for production-grade logs
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("🚀 Connected to: %s", engine.url)
