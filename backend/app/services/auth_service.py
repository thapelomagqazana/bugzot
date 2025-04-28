"""Business logic services for authentication operations."""

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from typing import Optional
from app.crud.user import (
    get_user_by_email,
    create_user,
    increment_login_attempts,
    reset_login_attempts,
)
from app.services.email import send_activation_email
from app.core.security import (
    create_access_token,
    create_activation_token,
    hash_password,
    validate_password_strength,
    verify_password,
    decode_access_token,
    get_token_jti,
)
from app.core.validation import is_disposable_email, validate_email_mx, sanitize_text
from app.core.rate_limiter import check_rate_limit
from app.core.constants import (
    LOGIN_RATE_LIMIT_PREFIX,
    REGISTER_RATE_LIMIT_PREFIX,
    TOKEN_BLACKLIST_PREFIX,
)
from app.core.redis import redis_client
from app.core import get_settings

settings = get_settings()
logger = logging.getLogger("audit")

DISPOSABLE_DOMAINS = {"tempmail.com", "10minutemail.com", "mailinator.com"}


def handle_register(db: Session, payload, ip: str):
    """
    Handle user registration including validation, creation, and sending activation email.
    """
    email = payload.email.strip().lower()
    full_name = sanitize_text(payload.full_name) if payload.full_name else None

    # Validate incoming registration request
    if not check_rate_limit(REGISTER_RATE_LIMIT_PREFIX, ip):
        logger.warning("[REGISTER_FAIL] Rate limit exceeded", extra={"ip": ip})
        raise HTTPException(status_code=429, detail="Too many requests from this IP.")

    if is_disposable_email(email, DISPOSABLE_DOMAINS):
        raise HTTPException(status_code=400, detail="Disposable email not allowed.")

    if not validate_email_mx(email):
        raise HTTPException(status_code=400, detail="Invalid email domain.")

    if get_user_by_email(db, email):
        logger.warning("[REGISTER_FAIL] Email already exists", extra={"email": email})
        raise HTTPException(status_code=409, detail="Email already registered.")

    if not validate_password_strength(payload.password):
        raise HTTPException(status_code=422, detail="Password is too weak.")

    # Create user
    hashed_pw = hash_password(payload.password)
    user = create_user(db, payload, hashed_pw, full_name)

    # Email activation
    token = create_activation_token(
        db, user.id, settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    send_activation_email(email, token)

    return user


def handle_login(db: Session, payload, ip: str):
    """
    Handle user authentication and return JWT token.
    """
    email = payload.email.strip().lower()

    # Validate login attempts
    if not check_rate_limit(LOGIN_RATE_LIMIT_PREFIX, ip):
        logger.warning("[LOGIN_FAIL] Rate limit exceeded", extra={"ip": ip})
        raise HTTPException(status_code=429, detail="Too many login attempts.")

    user = get_user_by_email(db, email)
    if not user or user.is_deleted:
        redis_client.incr(f"{LOGIN_RATE_LIMIT_PREFIX}:{ip}")
        redis_client.expire(f"{LOGIN_RATE_LIMIT_PREFIX}:{ip}", 60)
        logger.warning("[LOGIN_FAIL] Invalid credentials", extra={"ip": ip})
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    if not user.is_active:
        logger.warning("[LOGIN_FAIL] Inactive or unverified", extra={"ip": ip})
        raise HTTPException(status_code=403, detail="Inactive or unverified account.")

    if not verify_password(payload.password, user.hashed_password):
        increment_login_attempts(db, user)
        redis_client.incr(f"{LOGIN_RATE_LIMIT_PREFIX}:{ip}")
        redis_client.expire(f"{LOGIN_RATE_LIMIT_PREFIX}:{ip}", 60)
        logger.warning("[LOGIN_FAIL] Incorrect password", extra={"email": email})
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    reset_login_attempts(db, user)

    token = create_access_token(data={"sub": str(user.id)})

    logger.info("[LOGIN_SUCCESS] User logged in", extra={"email": email})
    return token, user


def handle_logout(token: str, user):
    """
    Handle user logout by blacklisting the JWT.
    """
    payload = decode_access_token(token)
    jti = get_token_jti(token)
    exp_timestamp = payload.get("exp")

    if not exp_timestamp:
        logger.error(
            "[LOGOUT_FAIL] Missing expiration in token", extra={"user_id": user.id}
        )
        raise HTTPException(status_code=400, detail="Token missing expiration")

    ttl = exp_timestamp - int(datetime.utcnow().timestamp())
    if ttl <= 0:
        logger.info("[LOGOUT] Token already expired", extra={"user_id": user.id})
        return

    redis_key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
    if redis_client:
        redis_client.setex(redis_key, ttl, "true")
        logger.info("[LOGOUT] Token blacklisted", extra={"user_id": user.id})
    else:
        logger.warning("[LOGOUT] Redis unavailable", extra={"user_id": user.id})
        raise HTTPException(status_code=503, detail="Logout temporarily unavailable")
