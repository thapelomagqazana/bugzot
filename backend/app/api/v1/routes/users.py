"""Routes for User management operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Path
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.users.user import User
from app.schemas.users import (
    UserOutPaginated,
    UserProfileOut,
    UserResponse,
    UserUpdateIn,
)
from app.api.v1.dependencies import require_admin
from app.core.log_decorator import audit_log
from app.services.user_service import (
    service_list_users,
    service_get_user_profile,
    service_delete_user,
    service_update_user_profile,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=UserOutPaginated, status_code=status.HTTP_200_OK)
@audit_log("List All Users")
async def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = Query(default=10, ge=0, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_dir: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
):
    """
    Endpoint to list all users with filters, search, pagination, and sorting.
    Admin-only access.
    """
    users, total = service_list_users(
        db,
        limit=limit,
        offset=offset,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return UserOutPaginated(total=total, limit=limit, offset=offset, data=users)


@router.get("/{user_id}", response_model=UserProfileOut, status_code=status.HTTP_200_OK)
@audit_log("View User Profile")
async def get_user_profile(
    request: Request,
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Endpoint to retrieve a user profile by ID.
    Admins can view any profile, users can view their own.
    """
    user = service_get_user_profile(
        db,
        current_user_id=current_user.id,
        target_user_id=user_id,
        current_user_role=current_user.role.name,
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
    Endpoint to update a user's profile by ID.
    Admin-only access. Partial updates supported.
    """
    user = service_update_user_profile(db, id, user_update)
    return user


@router.delete(
    "/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete (soft-delete) a user",
)
@audit_log("Delete User Profile")
async def delete_user_profile(
    id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Endpoint to soft-delete a user profile by ID.
    Admin-only access. Cannot delete yourself.
    """
    deleted_user = service_delete_user(
        db, target_user_id=id, acting_user_id=admin_user.id
    )
    return UserResponse.model_validate(deleted_user)
