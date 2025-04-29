from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.users.role import Role
from typing import List, Optional

def get_roles_paginated(
    db: Session,
    limit: int,
    offset: int,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    sort_dir: str = "desc"
) -> List[Role]:
    query = db.query(Role)

    if search:
        query = query.filter(Role.name.ilike(f"%{search.strip().lower()}%"))

    if is_active is not None:
        query = query.filter(Role.is_active == is_active)

    sort_column = Role.created_at.desc() if sort_dir == "desc" else Role.created_at.asc()

    return query.order_by(sort_column).offset(offset).limit(limit).all()


def count_roles(
    db: Session,
    search: Optional[str] = None,
    is_active: Optional[bool] = None
) -> int:
    query = db.query(Role)

    if search:
        query = query.filter(Role.name.ilike(f"%{search.strip().lower()}%"))

    if is_active is not None:
        query = query.filter(Role.is_active == is_active)

    return query.count()

