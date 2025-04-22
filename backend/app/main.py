from fastapi import FastAPI
from app.core import get_settings
from app.db import engine
# from app.db.init_db import seed_roles
from app.api.v1.routes import auth
# from app.api.v1.routes import bugs, auth, comments, users

# Load the configuration once
settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    debug=settings.DEBUG,
)

# seed_roles()

app.include_router(auth.router, prefix="/api/v1")
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(bugs.router, prefix="/api/v1/bugs", tags=["Bugs"])
# app.include_router(comments.router, prefix="/api/v1/comments", tags=["Comments"])

@app.get("/")
def health_check():
    """
    Basic health check endpoint to verify environment configuration.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }

@app.on_event("startup")
def log_db_info():
    print(f"🚀 Connected to: {engine.url}")
