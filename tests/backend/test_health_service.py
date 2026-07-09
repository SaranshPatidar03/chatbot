"""HealthService unit tests with mocked dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.health import DependencyStatus
from app.services.health import HealthService


@pytest.mark.asyncio
async def test_check_postgres_ok() -> None:
    service = HealthService()
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch("app.services.health.engine") as mock_engine:
        mock_engine.connect.return_value = mock_cm
        status = await service.check_postgres()

    assert status.name == "postgres"
    assert status.status == "ok"
    assert status.latency_ms is not None


@pytest.mark.asyncio
async def test_check_postgres_unavailable() -> None:
    service = HealthService()
    with patch("app.services.health.engine") as mock_engine:
        mock_engine.connect.side_effect = RuntimeError("connection refused")
        status = await service.check_postgres()
    assert status.status == "unavailable"
    assert "connection refused" in (status.detail or "")


@pytest.mark.asyncio
async def test_readiness_aggregates_checks() -> None:
    service = HealthService()
    with (
        patch.object(
            service,
            "check_postgres",
            AsyncMock(return_value=DependencyStatus(name="postgres", status="ok")),
        ),
        patch.object(
            service,
            "check_redis",
            AsyncMock(return_value=DependencyStatus(name="redis", status="ok")),
        ),
        patch.object(
            service,
            "check_chromadb",
            MagicMock(return_value=DependencyStatus(name="chromadb", status="ok")),
        ),
    ):
        result = await service.readiness()
    assert result.status == "ready"
    assert len(result.checks) == 3
