"""Phase 1/2 health endpoint tests."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.health import DependencyStatus, ReadinessResponse
from app.services.health import CURRENT_PHASE


@pytest.mark.asyncio
async def test_health_versioned() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["phase"] == CURRENT_PHASE
    assert CURRENT_PHASE == 14
    assert "version" in payload
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_health_root() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_when_dependencies_ok() -> None:
    ready = ReadinessResponse(
        status="ready",
        app="Knowledge Chatbot",
        version="0.1.0",
        phase=2,
        environment="development",
        checks=[
            DependencyStatus(name="postgres", status="ok", latency_ms=1.0),
            DependencyStatus(name="redis", status="ok", latency_ms=1.0),
            DependencyStatus(name="chromadb", status="ok", latency_ms=1.0),
        ],
    )
    with patch("app.api.routers.health.HealthService") as mock_cls:
        instance = mock_cls.return_value
        instance.readiness = AsyncMock(return_value=ready)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_ready_returns_503_when_not_ready() -> None:
    not_ready = ReadinessResponse(
        status="not_ready",
        app="Knowledge Chatbot",
        version="0.1.0",
        phase=2,
        environment="development",
        checks=[
            DependencyStatus(name="postgres", status="unavailable", detail="down"),
            DependencyStatus(name="redis", status="ok", latency_ms=1.0),
            DependencyStatus(name="chromadb", status="ok", latency_ms=1.0),
        ],
    )
    with patch("app.api.routers.health.HealthService") as mock_cls:
        instance = mock_cls.return_value
        instance.readiness = AsyncMock(return_value=not_ready)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
