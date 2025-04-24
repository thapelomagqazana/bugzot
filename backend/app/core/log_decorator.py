import functools
import logging
from fastapi import Request

logger = logging.getLogger("audit")

def audit_log(action: str):
    """
    Decorator to log audit events with user metadata.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request") or next((a for a in args if isinstance(a, Request)), None)
            if request:
                logger.info(
                    f"[AUDIT] {action}",
                    extra={
                        "ip": request.client.host,
                        "user_email": getattr(request.state, "user_email", "-"),
                        "request_id": getattr(request.state, "request_id", "-"),
                    }
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
