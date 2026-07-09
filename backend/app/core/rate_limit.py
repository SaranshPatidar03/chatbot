"""Redis-backed fixed-window rate limiting."""

from __future__ import annotations

import time
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.config import Settings, get_settings


@dataclass(slots=True)
class RateLimitResult:
    """Outcome of a rate-limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: int


class RateLimiter:
    """Simple fixed-window counter stored in Redis."""

    def __init__(
        self,
        redis: Redis,
        *,
        limit: int | None = None,
        window_seconds: int | None = None,
        settings: Settings | None = None,
    ) -> None:
        cfg = settings or get_settings()
        self.redis = redis
        self.limit = limit if limit is not None else cfg.rate_limit_requests
        self.window_seconds = (
            window_seconds if window_seconds is not None else cfg.rate_limit_window_seconds
        )

    async def check(self, key: str) -> RateLimitResult:
        """Increment the counter for ``key`` and return allow/deny status."""
        now = int(time.time())
        window = now // self.window_seconds
        redis_key = f"rl:{key}:{window}"
        pipe = self.redis.pipeline()
        pipe.incr(redis_key)
        pipe.expire(redis_key, self.window_seconds + 1)
        count, _ = await pipe.execute()
        count_int = int(count)
        reset_at = (window + 1) * self.window_seconds
        remaining = max(0, self.limit - count_int)
        return RateLimitResult(
            allowed=count_int <= self.limit,
            limit=self.limit,
            remaining=remaining,
            reset_at=reset_at,
        )
