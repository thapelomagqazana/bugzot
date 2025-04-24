from app.core.redis import redis_client
from app.core import get_settings

r = redis_client
settings = get_settings()

MAX_REQUESTS = 5
WINDOW_SECONDS = 60

def check_rate_limit(ip: str) -> bool:
    """
    Limit number of requests from a single IP within a fixed window.
    """
    if settings.ENVIRONMENT == "test" or settings.ENVIRONMENT == "development":
        return True  # skip rate limiting in tests
    key = f"rl:{ip}"
    current = r.get(key)
    if current and int(current) >= MAX_REQUESTS:
        return False
    r.incr(key)
    r.expire(key, WINDOW_SECONDS)
    return True
