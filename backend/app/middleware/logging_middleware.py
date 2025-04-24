from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging

class LoggingContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        ip = request.client.host
        ua = request.headers.get("user-agent", "")

        # Attach context to logger
        logging.LoggerAdapter(logging.getLogger(), {
            "ip": ip,
            "user_email": "-",  # You can override this in endpoints
            "request_id": request_id
        })

        response = await call_next(request)
        return response
