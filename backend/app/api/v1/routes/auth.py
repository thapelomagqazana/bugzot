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
    create_user, get_user_by_email, 
    increment_login_attempts, reset_login_attempts
)
from app.core.constants import (
    LOGIN_RATE_LIMIT_PREFIX, 
    REGISTER_RATE_LIMIT_PREFIX
)
from app.core.redis import redis_client
from app.db.session import get_db
from app.core import get_settings
from app.models.users.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest
)
from app.schemas.users import UserResponse 
from datetime import datetime

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger("audit")
DISPOSABLE_DOMAINS = {"tempmail.com", "10minutemail.com", "mailinator.com"}

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@audit_log("User Registration Attempt")
async def register_user(
    payload: UserRegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user_agent: Optional[str] = Header(None),
    honeypot: Optional[str] = Header(None),
) -> UserResponse:
    """
    Register a new user.

    - Normalize and validate inputs
    - Bot detection (honeypot)
    - IP rate limiting
    - Email domain + disposable check
    - Password strength + hashing
    - Create user and send activation email
    - Structured logging for auditing
    """
    ip = request.client.host
    email = payload.email.strip().lower()
    full_name = sanitize_text(payload.full_name) if payload.full_name else None

    # Honeypot bot detection
    if not check_honeypot_field(honeypot):
        logger.warning("[BOT] Honeypot triggered", extra={"ip": ip, "user_agent": user_agent})
        raise HTTPException(status_code=400, detail="Bot activity detected.")

    # Rate limiting
    if not check_rate_limit(REGISTER_RATE_LIMIT_PREFIX, ip):
        logger.warning("[RATELIMIT] Too many requests", extra={"ip": ip})
        raise HTTPException(status_code=429, detail="Too many requests from this IP.")

    # Disposable email check
    if is_disposable_email(email, DISPOSABLE_DOMAINS):
        raise HTTPException(status_code=400, detail="Disposable email addresses are not allowed.")

    # DNS MX check
    if not validate_email_mx(email):
        raise HTTPException(status_code=400, detail="Invalid email domain (MX check failed).")

    # Uniqueness check
    if get_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already registered.")

    # Password validation and hashing
    if not validate_password_strength(payload.password):
        raise HTTPException(status_code=422, detail="Password is too weak.")
    hashed_pw = hash_password(payload.password)

    # Create new user in DB
    new_user = create_user(db, payload, hashed_pw, full_name)

    # Email verification link
    token = create_activation_token(db, new_user.id, settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    send_activation_email(email, token)

    # Audit log
    logger.info(
        "[REGISTER] User registered",
        extra={
            "ip": ip,
            "user_email": email,
            "user_agent": user_agent,
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )

    return UserResponse.model_validate(new_user)


@router.post("/login")
@audit_log("User Login Attempt")
async def login_user(
    payload: UserLoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user_agent: Optional[str] = Header(None),
) -> TokenResponse:
    """
    Authenticate user and return JWT access token.

    - Normalize and validate credentials
    - Track failed attempts and rate limit
    - Structured audit logging
    """
    ip = request.client.host
    email = payload.email.strip().lower()

    # Rate limiting per IP
    rate_key = f"{LOGIN_RATE_LIMIT_PREFIX}:{ip}"
    if not check_rate_limit(LOGIN_RATE_LIMIT_PREFIX, ip):
        logger.warning("[RATELIMIT] Too many login attempts", extra={"ip": ip})
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    # Fetch user
    user = get_user_by_email(db, email=email)
    if not user or user.is_deleted:
        redis_client.incr(rate_key)
        redis_client.expire(rate_key, 60)
        logger.warning("[LOGIN_FAIL] Invalid credentials", extra={"ip": ip})
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    if not user.is_active:
        logger.warning("[LOGIN_FAIL] Account is inactive or unverified.", extra={"ip": ip})
        raise HTTPException(status_code=403, detail="Account is inactive or unverified.")

    if not verify_password(payload.password, user.hashed_password):
        logger.warning("[LOGIN_FAIL] Invalid credentials", extra={"ip": ip})
        increment_login_attempts(db, user)
        redis_client.incr(rate_key)
        redis_client.expire(rate_key, 60)
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    # Successful login
    reset_login_attempts(db, user)
    token = create_access_token(data={"sub": str(user.id)})

    # Log structured event
    logger.info(
        "[LOGIN] User logged in successfully",
        extra={
            "ip": ip,
            "user_email": user.email,
            "user_agent": user_agent,
            "request_id": getattr(request.state, "request_id", "-"),
        },
    )

    return TokenResponse(access_token=token, token_type=TOKEN_TYPE_BEARER)



@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@audit_log("User Logout Attempt")
async def logout_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
    user: Annotated[User, Depends(get_current_user)],
    user_agent: Optional[str] = Header(None),
) -> None:
    """
    Invalidate JWT access token by blacklisting its JTI in Redis.

    - Token must be valid
    - Token's expiration is used for TTL in Redis
    - Blacklisting ensures token reuse fails
    """
    ip = request.client.host
    try:
        payload = decode_access_token(token)
        jti = get_token_jti(token)
        exp_timestamp = payload.get("exp")

        if not exp_timestamp:
            raise HTTPException(status_code=400, detail="Token missing expiration")

        ttl = exp_timestamp - int(datetime.utcnow().timestamp())
        if ttl <= 0:
            logger.info("[LOGOUT] Token already expired", extra={"user_id": user.id, "ip": ip})
            return  # Already expired, consider it logged out

        redis_key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"

        if redis_client:
            redis_client.setex(redis_key, ttl, "true")
        else:
            logger.warning("[LOGOUT] Redis unavailable", extra={"user_id": user.id, "ip": ip})
            raise HTTPException(status_code=503, detail="Logout temporarily unavailable")

        logger.info(
            "[LOGOUT] Token blacklisted",
            extra={
                "user_id": user.id,
                "user_email": user.email,
                "ip": ip,
                "user_agent": user_agent,
                "request_id": getattr(request.state, 'request_id', None),
            },
        )

    except Exception as e:
        logger.error("[LOGOUT] Failed", exc_info=e)
        raise HTTPException(status_code=401, detail="Invalid token")


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
