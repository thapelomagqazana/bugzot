from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Schema for user data returned after registration or login."""

    id: int
    email: EmailStr
    full_name: str | None = None
    role_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

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
