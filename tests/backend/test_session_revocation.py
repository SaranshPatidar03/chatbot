"""Access token rejected after session revocation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_access_token_invalid_after_logout_all(client: AsyncClient) -> None:
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": "revoke@example.com", "password": "securepass123"},
    )
    assert signup.status_code == 201
    data = signup.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200

    logout_all = await client.post("/api/v1/auth/logout-all", headers=headers)
    assert logout_all.status_code == 200

    me_after = await client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 401
