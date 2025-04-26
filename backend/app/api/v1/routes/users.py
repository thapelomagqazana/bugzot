from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, selectinload
from typing import Optional
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.users.user import User
from app.schemas.users import UserOutPaginated
from app.api.v1.dependencies import require_admin
from app.core.log_decorator import audit_log

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=UserOutPaginated, status_code=status.HTTP_200_OK)
@audit_log("List All Users")
async def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = Query(
        default=10, ge=0, le=100, description="Number of users to return."
    ),
    offset: int = Query(0, ge=0, description="Starting offset for users."),
    search: Optional[str] = Query(None, description="Search by email or full name."),
    is_active: Optional[bool] = Query(
        None, description="Filter users by active status."
    ),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by."),
    sort_dir: Optional[str] = Query(
        "desc", regex="^(asc|desc)$", description="Sort direction."
    ),
):
    """
    List all users with pagination, optional search, and sorting.
    - Admins only.
    - Excludes soft-deleted users.
    """
    query = (
        db.query(User).options(selectinload(User.role)).filter(User.is_deleted == False)
    )

    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if sort_by not in {"email", "created_at", "full_name"}:
        sort_by = "created_at"

    sort_column = getattr(User, sort_by)
    if sort_dir == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()

    users = query.order_by(sort_column).offset(offset).limit(limit).all()
    total = query.count()

    return UserOutPaginated(total=total, limit=limit, offset=offset, data=users)
