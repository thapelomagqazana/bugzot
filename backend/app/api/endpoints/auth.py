import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Request
from app.repositories.base import BaseRepository
from app.deps import get_user_repository, get_current_user
from app.utils.security import verify_password
from app.utils.jwt import create_access_token
from app.core.config import settings
from app.schemas.auth import SignInRequest, TokenResponse
from app.db.models import User
from app.core.logging import logger
from datetime import timedelta


def get_request_metadata(request: Request):
    client_ip = request.client.host
    request_id = str(uuid.uuid4())
    return client_ip, request_id


router = APIRouter()


@router.post(
    "/signin",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Sign In",
    description="Authenticate a user with email and password. Returns a JWT token upon successful login.",
    responses={
        200: {"description": "Successfully authenticated."},
        401: {"description": "Invalid email or password."},
        422: {"description": "Validation error."}
    }
)
def signin(
    credentials: SignInRequest, 
    user_repo: BaseRepository = Depends(get_user_repository),
    request: Request = None
):
    client_ip, request_id = get_request_metadata(request)

    db_user = user_repo.get_by_email(credentials.email.lower())
    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    expires_in = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)  # Define token expiry duration
    access_token = create_access_token({"user_id": db_user.id, "role": db_user.role}, expires_in)
    logger.info(f"[{request_id}] User {client_ip} signed in: {credentials.email.lower()}")
    return {"access_token": access_token}


@router.post(
    "/signout",
    status_code=status.HTTP_200_OK,
    summary="User Sign Out",
    description="Sign out the currently authenticated user. For JWT-based auth, this is typically handled client-side.",
    responses={
        200: {"description": "Successfully signed out."},
        401: {"description": "Invalid or expired token."}
    }
)
def signout(
    user_repo: BaseRepository = Depends(get_user_repository),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    client_ip, request_id = get_request_metadata(request)
    logger.info(f"[{request_id}] User from {client_ip} with ID {current_user.id} signed out.")
    return {"detail": "Successfully signed out."}
