from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import auth, users
from app.db.models import Base
from app.db.session import engine
from app.core.config import settings

# Create tables (optional during development)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Management API",
    description="""
    ## Overview
    This API handles user authentication and management with full CRUD operations.
    
    ### Features:
    - **User Registration**
    - **User Authentication (JWT)**
    - **Role-based Access (admin/user)**
    - **User Update & Deletion**
    - **Logging with metadata (IP, request ID)**

    ### Authentication:
    - Use the `/auth/signin` endpoint to get your **JWT token**.
    - Add the token to the **Authorize** button in Swagger or include it in your headers like:
      ```
      Authorization: Bearer <your_token>
      ```

    ### Tags:
    - **Authentication**: Sign in and sign out.
    - **Users**: Manage users, only admins can manage others.
    """,
    version="1.0.0",
    contact={
        "name": "Your Team",
        "email": "support@example.com",
        "url": "https://example.com/support",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Enable CORS (Allow frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.BACKEND_CORS_ORIGINS],  # Allow React frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
