"""Shared dependencies used across version 1 API routes."""

from fastapi import Depends, HTTPException, status
from app.models.users.user import User
from app.core.security import get_current_user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active or current_user.role.name.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this resource.",
        )
    return current_user
