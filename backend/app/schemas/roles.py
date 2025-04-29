from pydantic import BaseModel
from datetime import datetime
from typing import List

class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_active: bool 
    is_system: bool
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True

class RoleOutPaginated(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[RoleOut]
