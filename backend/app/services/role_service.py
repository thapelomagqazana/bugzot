from sqlalchemy.orm import Session
from typing import List, Optional, Literal, Tuple
from app.crud.role import get_roles_paginated, count_roles
from app.models.users.role import Role

def list_roles_service(
    db: Session,
    limit: int = 10,
    offset: int = 0,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_dir: Literal["asc", "desc"] = "desc"
) -> Tuple[List[Role], int]:
    """
    Business logic for listing roles with pagination, filtering, and sorting.
    Returns (roles, total_count)
    """
    roles = get_roles_paginated(
        db,
        limit=limit,
        offset=offset,
        search=search,
        is_active=is_active,
        sort_dir=sort_dir,
    )
    total = count_roles(db, search=search, is_active=is_active)
    return roles, total
