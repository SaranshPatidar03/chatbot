"""HTTP rate limiting middleware backed by Redis."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.rate_limit import RateLimiter
from app.core.redis import get_redis

logger = get_logger(__name__)

_EXEMPT_PREFIXES = (
    "/health",
    "/ready",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply fixed-window rate limits per client IP for API traffic."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if any(path == prefix or path.startswith(f"{prefix}/") for prefix in _EXEMPT_PREFIXES):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        auth_prefix = f"{settings.app_api_prefix}/auth"
        is_auth_route = path.startswith(auth_prefix) or path.startswith("/auth/")
        limit = settings.auth_rate_limit_requests if is_auth_route else settings.rate_limit_requests
        try:
            redis = get_redis()
            result = await RateLimiter(
                redis,
                settings=settings,
                limit=limit,
            ).check(f"ip:{client_ip}")
        except Exception as exc:  # noqa: BLE001 — fail open if Redis unavailable
            logger.warning("rate_limit_check_failed", error=str(exc))
            return await call_next(request)

        if not result.allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result.reset_at),
                    "Retry-After": str(max(1, result.reset_at - int(time.time()))),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_at)
        return response
