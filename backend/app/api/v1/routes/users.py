"""Routes for managing user-related operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.security import get_current_user
from app.models.users.user import User
from app.schemas.auth import UserResponse
from app.db.session import get_db

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[UserResponse]:
    """
    List all users (admin only).
    """
    if current_user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list all users."
        )

    return db.query(User).filter(User.is_deleted == False).all()
