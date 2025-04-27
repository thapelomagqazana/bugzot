from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Path
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime, timezone
from app.db.session import get_db
from app.crud.user import get_user_by_email
from app.core.security import get_current_user
from app.crud.user import get_user_by_id
from app.models.users.user import User
from app.schemas.users import (
    UserOutPaginated, UserProfileOut,
    UserResponse, UserUpdateIn
)
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


@router.get("/{user_id}", response_model=UserProfileOut, status_code=status.HTTP_200_OK)
@audit_log("View User Profile")
async def get_user_profile(
    request: Request,
    user_id: int = Path(..., gt=0, description="ID of the user to fetch"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Fetch a user's profile.

    - Admins can view any profile.
    - Users can view their own profile only.
    """

    user = get_user_by_id(db, user_id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not (current_user.role.name.lower() == "admin" or current_user.id == user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return user

@router.put(
    "/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user profile",
)
@audit_log("Update User Profile")
async def update_user_profile(
    id: int,
    user_update: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Update a user's profile by ID. Admins only.
    Supports partial updates (PATCH-like behavior).
    """
    user = db.query(User).filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    # Optional fields: only update what is provided
    update_data = user_update.dict(exclude_unset=True)

    if "email" in update_data:
        # Uniqueness check
        if get_user_by_email(db, update_data["email"]):
            raise HTTPException(status_code=409, detail="Email already registered.")

    # Apply updates
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role_id or data constraint violation."
        )

    return user
