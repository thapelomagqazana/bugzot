from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator


class UserResponse(BaseModel):
    """Schema for user data returned after registration or login."""

    id: int
    email: EmailStr
    full_name: str | None = None
    role_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]

    class Config:
        """Enable ORM mode for Pydantic models."""

        from_attributes = True


class UserOutPaginated(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[UserResponse]


class UserProfileOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    role_id: int

    class Config:
        orm_mode = True


class UserUpdateIn(BaseModel):
    email: Optional[EmailStr] = Field(None, description="New email address.")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = Field(None, description="Activate/Deactivate user.")
    role_id: Optional[int] = Field(None, description="Change user's role.")

    class Config:
        from_attributes = True
        extra = "forbid"

    @validator("full_name")
    def full_name_must_not_be_whitespace(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("Full name must not be empty or only whitespace.")
        return v


class UserDeleteResponse(BaseModel):
    id: int
    email: str
    deleted_at: str  # ISO Timestamp
    message: str = "User account has been deactivated successfully."
