"""Redis-backed cache for query embedding vectors."""

from __future__ import annotations

import hashlib
import json

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)


def _cache_key(provider: str, model: str | None, query: str) -> str:
    digest = hashlib.sha256(f"{provider}:{model or ''}:{query}".encode()).hexdigest()
    return f"emb:q:{digest}"


async def get_cached_query_embedding(
    provider: str,
    model: str | None,
    query: str,
    *,
    settings: Settings | None = None,
) -> list[float] | None:
    """Return a cached embedding vector or ``None`` if missing/unavailable."""
    cfg = settings or get_settings()
    if not cfg.embedding_cache_enabled:
        return None
    try:
        redis = get_redis()
        raw = await redis.get(_cache_key(provider, model, query))
        if not raw:
            return None
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [float(value) for value in parsed]
    except Exception as exc:  # noqa: BLE001
        logger.debug("embedding_cache_get_failed", error=str(exc))
    return None


async def set_cached_query_embedding(
    provider: str,
    model: str | None,
    query: str,
    vector: list[float],
    *,
    settings: Settings | None = None,
) -> None:
    """Store a query embedding vector with TTL."""
    cfg = settings or get_settings()
    if not cfg.embedding_cache_enabled:
        return
    try:
        redis = get_redis()
        await redis.setex(
            _cache_key(provider, model, query),
            cfg.embedding_cache_ttl_seconds,
            json.dumps(vector),
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("embedding_cache_set_failed", error=str(exc))
