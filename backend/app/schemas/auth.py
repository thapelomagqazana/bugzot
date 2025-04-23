"""Schemas for user authentication and token handling."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, constr


class UserRegisterRequest(BaseModel):
    """Schema for user registration input."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: constr(max_length=255) | None = None


class UserResponse(BaseModel):
    """Schema for user data returned after registration or login."""

    id: int
    email: EmailStr
    full_name: str | None = None
    role_id: int
    is_active: bool
    created_at: datetime

    class Config:
        """Enable ORM mode for Pydantic models."""

        orm_mode = True  # allow returning ORM objects directly


class UserLoginRequest(BaseModel):
    """Schema for user login input."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
