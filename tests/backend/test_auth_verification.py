"""Email verification and session management tests."""

import pytest
from httpx import AsyncClient


async def _signup(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "securepass123", "full_name": "Verify User"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_verify_email(client: AsyncClient, monkeypatch) -> None:
    captured: list[str] = []

    async def fake_send(*, to_email: str, verification_token: str, settings=None) -> None:
        captured.append(verification_token)

    monkeypatch.setattr("app.services.auth.send_verification_email", fake_send)

    data = await _signup(client, "verify@example.com")
    assert data["user"]["is_verified"] is False
    assert captured

    headers = {"Authorization": f"Bearer {data['access_token']}"}
    verify = await client.post("/api/v1/auth/verify-email", json={"token": captured[0]})
    assert verify.status_code == 200

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["is_verified"] is True


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient) -> None:
    data = await _signup(client, "sessions@example.com")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    listed = await client.get("/api/v1/auth/sessions", headers=headers)
    assert listed.status_code == 200
    payload = listed.json()
    assert payload["total"] >= 1
    assert any(item["is_current"] for item in payload["items"])


@pytest.mark.asyncio
async def test_logout_all_devices(client: AsyncClient) -> None:
    data = await _signup(client, "logoutall@example.com")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    logout_all = await client.post("/api/v1/auth/logout-all", headers=headers)
    assert logout_all.status_code == 200

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": data["refresh_token"]},
    )
    assert refresh.status_code == 401
