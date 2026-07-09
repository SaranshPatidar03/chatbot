"""Async Redis client factory."""

from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    """Return a process-wide async Redis client."""
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """Close the cached Redis client."""
    client = get_redis()
    await client.aclose()
    get_redis.cache_clear()
