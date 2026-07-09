"""Chat API integration tests."""

import io
import json

import pytest
from httpx import AsyncClient


async def _signup_and_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "chat@example.com", "password": "securepass123", "full_name": "Chat User"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _parse_sse_payload(body: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    event_name = "message"
    for line in body.splitlines():
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            events.append((event_name, json.loads(line.split(":", 1)[1].strip())))
    return events


@pytest.mark.asyncio
async def test_chat_refusal_without_knowledge(client: AsyncClient) -> None:
    token = await _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/chats", headers=headers, json={})
    assert created.status_code == 201
    chat_id = created.json()["id"]

    async with client.stream(
        "POST",
        f"/api/v1/chats/{chat_id}/messages",
        headers=headers,
        json={"content": "What is the leave policy?"},
    ) as response:
        assert response.status_code == 200
        body = "".join([chunk async for chunk in response.aiter_text()])

    parsed = _parse_sse_payload(body)
    tokens = "".join(data["content"] for name, data in parsed if name == "token")
    assert "could not find this information" in tokens.lower()

    messages = await client.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)
    assert messages.status_code == 200
    items = messages.json()["items"]
    assert len(items) == 2
    assert items[-1]["role"] == "assistant"
    assert items[-1]["citations"] == []


@pytest.mark.asyncio
async def test_chat_grounded_response_with_citations(client: AsyncClient, mock_vector_indexing) -> None:
    token = await _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    files = {"files": ("policy.txt", io.BytesIO(b"Our leave policy grants 20 days per year."), "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert upload.status_code == 201

    created = await client.post("/api/v1/chats", headers=headers, json={})
    chat_id = created.json()["id"]

    async with client.stream(
        "POST",
        f"/api/v1/chats/{chat_id}/messages",
        headers=headers,
        json={"content": "How many leave days are granted?"},
    ) as response:
        assert response.status_code == 200
        body = "".join([chunk async for chunk in response.aiter_text()])

    parsed = _parse_sse_payload(body)
    citation_events = [data for name, data in parsed if name == "citations"]
    assert citation_events
    assert len(citation_events[0]["citations"]) >= 1

    tokens = "".join(data["content"] for name, data in parsed if name == "token")
    assert "20 days" in tokens.lower()

    messages = await client.get(f"/api/v1/chats/{chat_id}/messages", headers=headers)
    assistant = messages.json()["items"][-1]
    assert assistant["role"] == "assistant"
    assert len(assistant["citations"]) >= 1


@pytest.mark.asyncio
async def test_chat_crud(client: AsyncClient) -> None:
    token = await _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/chats", headers=headers, json={"title": "HR questions"})
    assert created.status_code == 201
    chat_id = created.json()["id"]

    listing = await client.get("/api/v1/chats", headers=headers)
    assert listing.status_code == 200
    assert any(item["id"] == chat_id for item in listing.json()["items"])

    updated = await client.patch(
        f"/api/v1/chats/{chat_id}",
        headers=headers,
        json={"title": "Updated title", "is_pinned": True},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated title"
    assert updated.json()["is_pinned"] is True

    deleted = await client.delete(f"/api/v1/chats/{chat_id}", headers=headers)
    assert deleted.status_code == 200
