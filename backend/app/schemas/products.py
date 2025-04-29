from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    is_deleted: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ProductOutPaginated(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[ProductOut]
