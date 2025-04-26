"""Schemas for user authentication and token handling."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.users.role import DEFAULT_ROLE_ID


class UserRegisterRequest(BaseModel):
    """Schema for user registration input."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=100)
    role_id: int = Field(default=DEFAULT_ROLE_ID)
    active: bool = Field(default=True)


class UserLoginRequest(BaseModel):
    """Schema for user login input."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
