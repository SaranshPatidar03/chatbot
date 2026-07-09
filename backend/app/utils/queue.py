"""Enqueue background jobs via ARQ."""

from __future__ import annotations

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def enqueue_ingest(document_id: str) -> bool:
    """Queue document ingestion. Returns False if Redis is unavailable."""
    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.arq_redis_url)
    redis_settings.conn_retries = 0
    try:
        redis = await create_pool(redis_settings)
        await redis.enqueue_job("ingest_document", document_id)
        await redis.close()
        return True
    except Exception as exc:
        logger.warning("ingest_enqueue_failed", document_id=document_id, error=str(exc))
        return False
