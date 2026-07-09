"""Background workers (ARQ) — job implementations expand in Phase 5–6."""

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.workers.ingest import ingest_document


async def ping_worker(_ctx: dict) -> str:
    """Simple worker health job used in Phase 1 wiring."""
    return "pong"


class WorkerSettings:
    """ARQ worker settings."""

    functions = [ping_worker, ingest_document]
    redis_settings = RedisSettings.from_dsn(get_settings().arq_redis_url)
    max_jobs = 10
    job_timeout = 60 * 30
