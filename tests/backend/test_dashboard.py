"""Dashboard summary API integration tests."""

import pytest
from httpx import AsyncClient


async def _signup(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "securepass123", "full_name": "Dash User"},
    )
    assert response.status_code == 201
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.mark.asyncio
async def test_dashboard_summary_empty(client: AsyncClient) -> None:
    headers = await _signup(client, "dash-empty@example.com")
    response = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["document_count"] == 0
    assert payload["chat_count"] == 0
    assert payload["storage_bytes"] == 0
    assert payload["documents_processing"] == 0
    assert payload["recent_documents"] == []
    assert payload["recent_chats"] == []


@pytest.mark.asyncio
async def test_dashboard_summary_with_chat(client: AsyncClient) -> None:
    headers = await _signup(client, "dash-chat@example.com")
    create = await client.post(
        "/api/v1/chats",
        headers=headers,
        json={"title": "Test chat"},
    )
    assert create.status_code == 201

    response = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["chat_count"] == 1
    assert len(payload["recent_chats"]) == 1
    assert payload["recent_chats"][0]["title"] == "Test chat"
