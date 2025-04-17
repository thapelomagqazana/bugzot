from fastapi import FastAPI
from app.api.v1.routes import bugs, auth, comments, users

app = FastAPI(title="BugZot - Bug Tracker")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(bugs.router, prefix="/api/v1/bugs", tags=["Bugs"])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["Comments"])
