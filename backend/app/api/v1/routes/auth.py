"""Routes for managing auth-related operations."""

from typing import Optional, Annotated
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from app.core.constants import TOKEN_TYPE_BEARER
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    validate_password_strength,
    create_activation_token,
    get_current_user,
    decode_access_token,
    oauth2_scheme,
    get_token_jti,
    TOKEN_BLACKLIST_PREFIX,
)
from app.core.validation import (
    is_disposable_email,
    validate_email_mx,
    sanitize_text,
    check_honeypot_field,
)
from app.core.rate_limiter import check_rate_limit
from app.services.email import send_activation_email
from app.core.log_decorator import audit_log
from app.crud.user import (
    create_user,
    get_user_by_email,
    increment_login_attempts,
    reset_login_attempts,
)
from app.core.constants import LOGIN_RATE_LIMIT_PREFIX, REGISTER_RATE_LIMIT_PREFIX
from app.core.redis import redis_client
from app.db.session import get_db
from app.core import get_settings
from app.models.users.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest
from app.schemas.users import UserResponse
from datetime import datetime
from app.services.auth_service import handle_register, handle_login, handle_logout


settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("audit")
DISPOSABLE_DOMAINS = {"tempmail.com", "10minutemail.com", "mailinator.com"}


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@audit_log("User Registration Attempt")
async def register_user(
    payload: UserRegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user_agent: Optional[str] = Header(None),
    honeypot: Optional[str] = Header(None),
):
    ip = request.client.host
    email = payload.email.strip().lower()

    # Honeypot check (can stay here if very lightweight)
    if not check_honeypot_field(honeypot):
        logger.warning(
            "[BOT] Honeypot triggered", extra={"ip": ip, "user_agent": user_agent}
        )
        raise HTTPException(status_code=400, detail="Bot activity detected.")

    user = handle_register(db, payload, ip)

    logger.info(
        "[REGISTER] User registered",
        extra={"ip": ip, "user_email": email, "user_agent": user_agent},
    )
    return UserResponse.model_validate(user)


@router.post("/login")
@audit_log("User Login Attempt")
async def login_user(
    payload: UserLoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user_agent: Optional[str] = Header(None),
):
    ip = request.client.host
    access_token, user = handle_login(db, payload, ip)

    logger.info(
        "[LOGIN] User logged in",
        extra={"ip": ip, "user_email": user.email, "user_agent": user_agent},
    )
    return TokenResponse(access_token=access_token, token_type=TOKEN_TYPE_BEARER)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@audit_log("User Logout Attempt")
async def logout_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
    user: Annotated[User, Depends(get_current_user)],
    user_agent: Optional[str] = Header(None),
):
    ip = request.client.host
    handle_logout(token, user)

    logger.info(
        "[LOGOUT] User logged out",
        extra={"ip": ip, "user_email": user.email, "user_agent": user_agent},
    )
    return


@router.get("/me", response_model=UserResponse)
@audit_log("Fetch Current User Info")
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None),
) -> UserResponse:
    """
    Returns info about the currently authenticated user.

    - Requires valid JWT Bearer Token
    - Includes IP logging and user agent
    - Returns sanitized user info
    """

    logger.info(
        "[GET_ME] User info fetched",
        extra={
            "ip": request.client.host,
            "user_id": current_user.id,
            "user_email": current_user.email,
            "user_agent": user_agent,
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )

    return current_user
