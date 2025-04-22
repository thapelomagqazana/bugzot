from pydantic import BaseModel, EmailStr, Field, constr
from datetime import datetime

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: constr(max_length=255) | None = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role_id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True  # allow returning ORM objects directly
