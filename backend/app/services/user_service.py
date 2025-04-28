"""Business logic services for User operations."""

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.crud.user import (
    get_user_by_id,
    get_user_by_email,
    list_users,
    update_user_fields,
    soft_delete_user,
)
from app.schemas.users import UserUpdateIn
from datetime import datetime, timezone

logger = logging.getLogger("audit")


def service_list_users(db: Session, **filters):
    """
    Business service to list users with optional filtering and sorting.
    """
    users, total = list_users(db, **filters)
    logger.info("[USER_LIST] Listed users", extra={"user_count": len(users)})
    return users, total


def service_get_user_profile(
    db: Session, current_user_id: int, target_user_id: int, current_user_role: str
):
    """
    Business service to retrieve user profile.
    Admins can view any profile; users can view only their own.
    """
    user = get_user_by_id(db, user_id=target_user_id)
    if not user:
        logger.warning(
            "[USER_FETCH_FAIL] User not found", extra={"target_user_id": target_user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not (current_user_role.lower() == "admin" or current_user_id == target_user_id):
        logger.warning(
            "[ACCESS_DENIED] Unauthorized profile access attempt",
            extra={
                "current_user_id": current_user_id,
                "target_user_id": target_user_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    logger.info(
        "[USER_FETCH] User profile fetched", extra={"target_user_id": target_user_id}
    )
    return user


def service_update_user_profile(db: Session, id: int, user_update: UserUpdateIn):
    """
    Business service to update a user's profile.
    Ensures email uniqueness check and updates provided fields.
    """
    user = get_user_by_id(db, user_id=id)
    if not user:
        logger.warning("[USER_UPDATE_FAIL] User not found", extra={"user_id": id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    update_data = user_update.dict(exclude_unset=True)

    if "email" in update_data:
        existing_user = get_user_by_email(db, update_data["email"])
        if existing_user and existing_user.id != id:
            logger.warning(
                "[EMAIL_CONFLICT] Email already taken",
                extra={"email": update_data["email"]},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered."
            )

    user.updated_at = datetime.now(timezone.utc)
    updated_user = update_user_fields(db, user, update_data)

    logger.info("[USER_UPDATE] User profile updated", extra={"user_id": id})
    return updated_user


def service_delete_user(db: Session, target_user_id: int, acting_user_id: int):
    """
    Business service to soft-delete a user.
    Prevents self-deletion by admin.
    """
    if target_user_id == acting_user_id:
        logger.warning(
            "[SELF_DELETE_ATTEMPT] Admin tried deleting self",
            extra={"admin_user_id": acting_user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself."
        )

    deleted_user = soft_delete_user(db, target_user_id)
    if not deleted_user:
        logger.warning(
            "[USER_DELETE_FAIL] User not found",
            extra={"target_user_id": target_user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    logger.info(
        "[USER_DELETE] User soft-deleted", extra={"deleted_user_id": target_user_id}
    )
    return deleted_user
