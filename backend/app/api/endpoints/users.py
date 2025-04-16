import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Request
from typing import List

from app.repositories.base import BaseRepository
from app.deps import get_user_repository, get_current_user
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.db.models import User
from app.core.logging import logger


def get_request_metadata(request: Request):
    client_ip = request.client.host
    request_id = str(uuid.uuid4())
    return client_ip, request_id


router = APIRouter()


@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Register a new user account. Fails if email is already in use.",
    responses={
        201: {"description": "User created successfully."},
        400: {"description": "Email already registered."},
        422: {"description": "Validation error."}
    }
)
def create_user(
    user: UserCreate, 
    user_repo: BaseRepository = Depends(get_user_repository),
    request: Request = None
):
    client_ip, request_id = get_request_metadata(request)

    existing_user = user_repo.get_by_email(user.email.lower())
    if existing_user:
        logger.warning(
            f"[{request_id}] Duplicate email registration attempt from {client_ip}: {user.email}"
        )
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    new_user = user_repo.create(user.dict())
    logger.info(
        f"[{request_id}] User created from {client_ip} with ID {new_user.id} and email {new_user.email}"
    )
    return new_user


@router.get(
    "/",
    response_model=List[UserOut],
    summary="List Users",
    description="Retrieve a paginated list of all registered users.",
    responses={
        200: {"description": "List of users returned successfully."},
        422: {"description": "Validation error on pagination parameters."}
    }
)
def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000), 
    user_repo: BaseRepository = Depends(get_user_repository),
    request: Request = None
):
    client_ip, request_id = get_request_metadata(request)

    users = user_repo.get_all(skip=skip, limit=limit)
    logger.info(f"[{request_id}] {len(users)} users fetched by {client_ip}.")
    return users


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Get User",
    description="Retrieve the details of a specific user by ID.",
    responses={
        200: {"description": "User details returned successfully."},
        404: {"description": "User not found."}
    }
)
def read_user(
    user_id: int = Path(..., gt=0),
    user_repo: BaseRepository = Depends(get_user_repository),
    current_user_id: int = Depends(get_current_user),
    request: Request = None
):
    client_ip, request_id = get_request_metadata(request)

    db_user = user_repo.get_by_id(user_id)
    if not db_user:
        logger.warning(f"[{request_id}] User ID {user_id} not found. Request from {client_ip}.")
        raise HTTPException(status_code=404, detail="User not found.")
    
    logger.info(f"[{request_id}] User ID {user_id} fetched by {client_ip}.")
    return db_user


@router.put(
    "/{user_id}",
    response_model=UserOut,
    summary="Update User",
    description="Update a user's details. Only the user or an admin can perform this action.",
    responses={
        200: {"description": "User updated successfully."},
        403: {"description": "Unauthorized to update this user."},
        404: {"description": "User not found."}
    }
)
def update_user(
    user_id: int,
    updates: UserUpdate,
    user_repo: BaseRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    client_ip, request_id = get_request_metadata(request)

    db_user = user_repo.get_by_id(user_id)
    if not db_user:
        logger.warning(f"[{request_id}] Attempted update on non-existent user ID {user_id} from {client_ip}.")
        raise HTTPException(status_code=404, detail="User not found.")
    
    if user_id != current_user.id and current_user.role != "admin":
        logger.warning(
            f"[{request_id}] Unauthorized update attempt on user ID {user_id} by user ID {current_user.id} from {client_ip}."
        )
        raise HTTPException(status_code=403, detail="Unauthorized to update this user.")

    updated_user = user_repo.update(user_id, updates.dict(exclude_unset=True))
    logger.info(f"[{request_id}] User ID {user_id} updated successfully by {client_ip}.")
    return updated_user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Delete a user account. Only the user or an admin can delete an account.",
    responses={
        204: {"description": "User deleted successfully."},
        403: {"description": "Unauthorized to delete this user."},
        404: {"description": "User not found."}
    }
)
def delete_user(
    user_id: int,
    user_repo: BaseRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    client_ip, request_id = get_request_metadata(request)

    db_user = user_repo.get_by_id(user_id)
    if not db_user:
        logger.warning(f"[{request_id}] Attempted deletion of non-existent user ID {user_id} from {client_ip}.")
        raise HTTPException(status_code=404, detail="User not found.")

    if user_id != current_user.id and current_user.role != "admin":
        logger.warning(
            f"[{request_id}] Unauthorized deletion attempt on user ID {user_id} by user ID {current_user.id} from {client_ip}."
        )
        raise HTTPException(status_code=403, detail="Unauthorized to delete this user.")

    user_repo.delete(user_id)
    logger.info(f"[{request_id}] User ID {user_id} deleted successfully by {client_ip}.")
