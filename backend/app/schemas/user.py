"""
Pydantic schemas for User model.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


# Schema for creating a new user
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[str] = Field(default="user")  # Added role with default

    @field_validator('name')
    @classmethod
    def name_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be blank or only spaces")
        return v

    @field_validator('password')
    @classmethod
    def password_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError("Password cannot be blank or only spaces")
        if len(v.strip()) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


# Schema for returning user data (output)
class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str  # Added role
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        model_config = {
            "from_attributes": True
        }  # Tells Pydantic to convert ORM objects to JSON


# Schema for updating an existing user
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None  # Added role

    @field_validator('email')
    @classmethod
    def strip_email(cls, v):
        return v.strip() if v else v
