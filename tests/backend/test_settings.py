"""User settings API integration tests."""

import pytest
from httpx import AsyncClient


async def _signup(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "securepass123", "full_name": "Settings User"},
    )
    assert response.status_code == 201
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.mark.asyncio
async def test_get_settings_after_signup(client: AsyncClient) -> None:
    headers = await _signup(client, "settings-get@example.com")
    response = await client.get("/api/v1/settings", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["llm_provider"] == "ollama"
    assert payload["llm_model"] == "llama3"
    assert payload["embedding_provider"] == "ollama"
    assert payload["top_k"] == 8
    assert payload["allow_general_knowledge"] is False


@pytest.mark.asyncio
async def test_update_settings(client: AsyncClient) -> None:
    headers = await _signup(client, "settings-patch@example.com")
    response = await client.patch(
        "/api/v1/settings",
        headers=headers,
        json={
            "llm_model": "mistral",
            "temperature": 0.4,
            "top_k": 12,
            "system_prompt": "Answer only from context.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["llm_model"] == "mistral"
    assert payload["temperature"] == 0.4
    assert payload["top_k"] == 12
    assert payload["system_prompt"] == "Answer only from context."

    again = await client.get("/api/v1/settings", headers=headers)
    assert again.json()["llm_model"] == "mistral"


@pytest.mark.asyncio
async def test_settings_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/settings")
    assert response.status_code == 401
