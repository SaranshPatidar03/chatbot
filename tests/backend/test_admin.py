"""Admin API integration tests."""

import pytest
from httpx import AsyncClient

from app.core.config import Settings, get_settings


@pytest.fixture
def admin_settings(monkeypatch):
    get_settings.cache_clear()
    settings = Settings(_env_file=(), initial_admin_email="admin@example.com")
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.auth.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.admin.get_settings", lambda: settings)
    yield settings
    get_settings.cache_clear()


async def _admin_token(client: AsyncClient, admin_settings) -> str:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "admin@example.com", "password": "securepass123", "full_name": "Admin"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "platform_admin"
    return body["access_token"]


@pytest.mark.asyncio
async def test_non_admin_forbidden(client: AsyncClient) -> None:
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "user@example.com", "password": "securepass123", "full_name": "User"},
    )
    token = signup.json()["access_token"]
    response = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_users(client: AsyncClient, admin_settings) -> None:
    token = await _admin_token(client, admin_settings)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any(item["email"] == "admin@example.com" for item in body["items"])


@pytest.mark.asyncio
async def test_admin_storage_and_system(client: AsyncClient, admin_settings) -> None:
    token = await _admin_token(client, admin_settings)
    headers = {"Authorization": f"Bearer {token}"}

    storage = await client.get("/api/v1/admin/storage/summary", headers=headers)
    assert storage.status_code == 200
    assert "total_bytes" in storage.json()

    health = await client.get("/api/v1/admin/system/health", headers=headers)
    assert health.status_code == 200
    assert "checks" in health.json()

    config = await client.get("/api/v1/admin/system/config", headers=headers)
    assert config.status_code == 200
    assert config.json()["default_llm_provider"] in {"openai", "ollama"}


@pytest.mark.asyncio
async def test_admin_audit_and_analytics(client: AsyncClient, admin_settings) -> None:
    token = await _admin_token(client, admin_settings)
    headers = {"Authorization": f"Bearer {token}"}

    audit = await client.get("/api/v1/admin/audit-logs", headers=headers)
    assert audit.status_code == 200
    assert audit.json()["total"] >= 1

    summary = await client.get("/api/v1/admin/analytics/summary", headers=headers)
    assert summary.status_code == 200
    assert "total_events" in summary.json()

    events = await client.get("/api/v1/admin/analytics/events", headers=headers)
    assert events.status_code == 200
