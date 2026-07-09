"""Health / readiness service — probes critical dependencies."""

from __future__ import annotations

import time
from typing import Literal

from sqlalchemy import text

from app import __version__
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.db.session import engine
from app.embeddings.store import VectorStore
from app.schemas.health import DependencyStatus, HealthResponse, ReadinessResponse

logger = get_logger(__name__)

CURRENT_PHASE = 14


class HealthService:
    """Aggregate liveness and readiness probes."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def liveness(self) -> HealthResponse:
        return HealthResponse(
            status="ok",
            app=self.settings.app_name,
            version=__version__,
            phase=CURRENT_PHASE,
            environment=self.settings.app_env,
        )

    async def check_postgres(self) -> DependencyStatus:
        started = time.perf_counter()
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            latency = (time.perf_counter() - started) * 1000
            return DependencyStatus(
                name="postgres",
                status="ok",
                latency_ms=round(latency, 2),
            )
        except Exception as exc:  # noqa: BLE001 — readiness must never raise
            latency = (time.perf_counter() - started) * 1000
            logger.warning("postgres_health_failed", error=str(exc))
            return DependencyStatus(
                name="postgres",
                status="unavailable",
                latency_ms=round(latency, 2),
                detail=str(exc),
            )

    async def check_redis(self) -> DependencyStatus:
        started = time.perf_counter()
        try:
            client = get_redis()
            pong = await client.ping()
            latency = (time.perf_counter() - started) * 1000
            if pong:
                return DependencyStatus(
                    name="redis",
                    status="ok",
                    latency_ms=round(latency, 2),
                )
            return DependencyStatus(
                name="redis",
                status="degraded",
                latency_ms=round(latency, 2),
                detail="PING returned falsy response",
            )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - started) * 1000
            logger.warning("redis_health_failed", error=str(exc))
            return DependencyStatus(
                name="redis",
                status="unavailable",
                latency_ms=round(latency, 2),
                detail=str(exc),
            )

    def check_chromadb(self) -> DependencyStatus:
        started = time.perf_counter()
        try:
            store = VectorStore(self.settings)
            ok = store.heartbeat()
            latency = (time.perf_counter() - started) * 1000
            if ok:
                return DependencyStatus(
                    name="chromadb",
                    status="ok",
                    latency_ms=round(latency, 2),
                )
            return DependencyStatus(
                name="chromadb",
                status="unavailable",
                latency_ms=round(latency, 2),
                detail="Heartbeat failed",
            )
        except Exception as exc:  # noqa: BLE001
            latency = (time.perf_counter() - started) * 1000
            logger.warning("chromadb_health_failed", error=str(exc))
            return DependencyStatus(
                name="chromadb",
                status="unavailable",
                latency_ms=round(latency, 2),
                detail=str(exc),
            )

    async def readiness(self) -> ReadinessResponse:
        checks = [
            await self.check_postgres(),
            await self.check_redis(),
            self.check_chromadb(),
        ]
        overall: Literal["ready", "not_ready"] = (
            "ready" if all(c.status == "ok" for c in checks) else "not_ready"
        )
        return ReadinessResponse(
            status=overall,
            app=self.settings.app_name,
            version=__version__,
            phase=CURRENT_PHASE,
            environment=self.settings.app_env,
            checks=checks,
        )
