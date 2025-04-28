"""Core constants used throughout the application."""

# Token type constant (used in authentication response schema)
TOKEN_TYPE_BEARER = "bearer"  # noqa: S105
LOGIN_RATE_LIMIT_PREFIX = "login:rate"
REGISTER_RATE_LIMIT_PREFIX = "register:rate"
TOKEN_BLACKLIST_PREFIX = "blacklist:"
