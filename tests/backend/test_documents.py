"""Document API integration tests."""

import io

import pytest
from httpx import AsyncClient


async def _signup_and_token(client: AsyncClient) -> str:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": "docs@example.com", "password": "securepass123", "full_name": "Doc User"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_upload_list_delete_document(client: AsyncClient) -> None:
    token = await _signup_and_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    files = {"files": ("policy.txt", io.BytesIO(b"Our leave policy grants 20 days per year."), "text/plain")}
    upload = await client.post("/api/v1/documents/upload", headers=headers, files=files)
    assert upload.status_code == 201
    uploaded = upload.json()
    assert len(uploaded) == 1
    document_id = uploaded[0]["id"]
    assert uploaded[0]["status"] in {"pending", "processing", "ready"}

    listing = await client.get("/api/v1/documents", headers=headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] >= 1
    assert any(item["id"] == document_id for item in body["items"])

    detail = await client.get(f"/api/v1/documents/{document_id}", headers=headers)
    assert detail.status_code == 200

    # Ingest runs inline when Redis unavailable in tests
    content = await client.get(f"/api/v1/documents/{document_id}/content", headers=headers)
    assert content.status_code == 200
    assert "leave policy" in content.json()["text"].lower()

    detail_after_ingest = await client.get(f"/api/v1/documents/{document_id}", headers=headers)
    assert detail_after_ingest.status_code == 200
    assert detail_after_ingest.json()["status"] == "ready"
    assert detail_after_ingest.json()["chunk_count"] >= 1

    deleted = await client.delete(f"/api/v1/documents/{document_id}", headers=headers)
    assert deleted.status_code == 200

    missing = await client.get(f"/api/v1/documents/{document_id}", headers=headers)
    assert missing.status_code == 404
