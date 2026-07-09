"""Search API integration tests."""

import io

import pytest
from httpx import AsyncClient


async def _signup_and_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "search@example.com", "password": "securepass123", "full_name": "Search User"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_search_returns_indexed_chunks(client: AsyncClient, mock_vector_indexing) -> None:
    token = await _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    files = {"files": ("policy.txt", io.BytesIO(b"Our leave policy grants 20 days per year."), "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert upload.status_code == 201
    document_id = upload.json()[0]["id"]

    detail = await client.get(f"/api/v1/documents/{document_id}", headers=headers)
    assert detail.json()["status"] == "ready"

    search = await client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "leave policy", "mode": "hybrid"},
    )
    assert search.status_code == 200
    body = search.json()
    assert body["mode"] == "hybrid"
    assert body["has_sufficient_context"] is True
    assert len(body["results"]) >= 1
    assert "leave policy" in body["results"][0]["content"].lower()
    assert body["results"][0]["document_id"] == document_id


@pytest.mark.asyncio
async def test_search_keyword_mode(client: AsyncClient, mock_vector_indexing) -> None:
    token = await _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    files = {"files": ("notes.txt", io.BytesIO(b"Quarterly revenue increased by 12 percent."), "text/plain")}
    await client.post("/api/v1/documents/upload", headers=headers, files=files)

    search = await client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "revenue", "mode": "keyword"},
    )
    assert search.status_code == 200
    assert len(search.json()["results"]) >= 1


@pytest.mark.asyncio
async def test_search_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/search", json={"query": "test"})
    assert response.status_code == 401
