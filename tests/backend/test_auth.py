"""Authentication API integration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_login_me_logout(client: AsyncClient) -> None:
    signup = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "alice@example.com",
            "password": "securepass123",
            "full_name": "Alice Example",
        },
    )
    assert signup.status_code == 201
    signup_data = signup.json()
    assert signup_data["token_type"] == "bearer"
    assert signup_data["user"]["email"] == "alice@example.com"
    assert "access_token" in signup_data
    assert "refresh_token" in signup_data

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "securepass123"},
    )
    assert login.status_code == 200
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["full_name"] == "Alice Example"

    patch = await client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"full_name": "Alice Updated"},
    )
    assert patch.status_code == 200
    assert patch.json()["full_name"] == "Alice Updated"

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 200
    refreshed = refresh.json()
    assert refreshed["access_token"]
    assert refreshed["refresh_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {refreshed['access_token']}"},
        json={"refresh_token": refreshed["refresh_token"]},
    )
    assert logout.status_code == 200
    assert logout.json()["message"]

    refresh_after = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refreshed["refresh_token"]},
    )
    assert refresh_after.status_code == 401


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "securepass123"}
    first = await client.post("/api/v1/auth/signup", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/auth/signup", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "bob@example.com", "password": "securepass123"},
    )
    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "wrongpassword"},
    )
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_forgot_password_always_returns_message(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "missing@example.com"},
    )
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-valid-token", "password": "newpassword123"},
    )
    assert response.status_code == 400
