import logging
import time
from collections.abc import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("backend.requests")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("%s %s → %d (%.1fms)", request.method, request.url.path, response.status_code, elapsed_ms)
            return response
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception("%s %s → ERROR (%.1fms)", request.method, request.url.path, elapsed_ms)
            raise
