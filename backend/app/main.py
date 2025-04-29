"""FastAPI application entry point and environment configuration checker."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.routes import auth, users, roles
from app.core.logging_config import setup_logging
from app.middleware.logging_middleware import LoggingContextMiddleware
from app.core import get_settings
from app.db import engine
import logging

# Configuration loading
settings = get_settings()
setup_logging()

VERSION_ONE_PREFIX = "/api/v1"

# CORS Configuration
CORS_ORIGINS = [settings.BACKEND_CORS_ORIGINS or "*"]

# FastAPI app creation
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)

# Middleware registration
app.add_middleware(LoggingContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router registration
app.include_router(auth.router, prefix=VERSION_ONE_PREFIX)
app.include_router(users.router, prefix=VERSION_ONE_PREFIX)
app.include_router(roles.router, prefix=VERSION_ONE_PREFIX)


@app.get("/", tags=["Health"])
def health_check() -> dict:
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "message": "BugZot API is up!",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }

# Modern Lifespan Event Handling (instead of deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # --- Startup ---
    log_database_info()

    yield  # The application runs while suspended here

    # --- Shutdown (optional future tasks like cleanup, metrics flush) ---
    # logger.info("App shutdown complete.")

app.router.lifespan_context = lifespan


def log_database_info() -> None:
    """Log database connection info securely."""
    logger = logging.getLogger("startup")
    # Hide sensitive parts like username/password
    safe_db_url = engine.url.set(password="***", username="***")
    logger.info(
        "🚀 Connected to database",
        extra={"db_url": str(safe_db_url)},
    )
