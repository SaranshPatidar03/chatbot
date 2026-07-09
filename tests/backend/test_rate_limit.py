"""Rate limiter tests with fake Redis pipeline."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.rate_limit import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit() -> None:
    redis = MagicMock()
    pipe = MagicMock()
    pipe.incr = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock(return_value=[1, True])
    redis.pipeline.return_value = pipe

    limiter = RateLimiter(redis, limit=5, window_seconds=60)
    result = await limiter.check("user:1")
    assert result.allowed is True
    assert result.remaining == 4
    assert result.limit == 5


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit() -> None:
    redis = MagicMock()
    pipe = MagicMock()
    pipe.incr = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock(return_value=[6, True])
    redis.pipeline.return_value = pipe

    limiter = RateLimiter(redis, limit=5, window_seconds=60)
    result = await limiter.check("user:1")
    assert result.allowed is False
    assert result.remaining == 0
