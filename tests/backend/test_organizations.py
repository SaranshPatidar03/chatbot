"""Organization API integration tests."""

import pytest
from httpx import AsyncClient


async def _signup(client: AsyncClient, email: str, name: str) -> str:
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "securepass123", "full_name": name},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_list_organizations(client: AsyncClient) -> None:
    token = await _signup(client, "owner@example.com", "Owner")
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Acme Research", "description": "Team docs"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["name"] == "Acme Research"
    assert body["slug"] == "acme-research"
    assert body["my_role"] == "owner"
    assert body["member_count"] == 1

    listing = await client.get("/api/v1/organizations", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


@pytest.mark.asyncio
async def test_invite_member_and_list_members(client: AsyncClient) -> None:
    owner_token = await _signup(client, "owner2@example.com", "Owner")
    member_token = await _signup(client, "member2@example.com", "Member")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    create = await client.post(
        "/api/v1/organizations",
        headers=owner_headers,
        json={"name": "Shared Lab"},
    )
    org_id = create.json()["id"]

    invite = await client.post(
        f"/api/v1/organizations/{org_id}/members",
        headers=owner_headers,
        json={"email": "member2@example.com", "role": "member"},
    )
    assert invite.status_code == 201
    assert invite.json()["email"] == "member2@example.com"

    members = await client.get(f"/api/v1/organizations/{org_id}/members", headers=owner_headers)
    assert members.status_code == 200
    assert members.json()["total"] == 2

    member_headers = {"Authorization": f"Bearer {member_token}"}
    detail = await client.get(f"/api/v1/organizations/{org_id}", headers=member_headers)
    assert detail.status_code == 200
    assert detail.json()["my_role"] == "member"


@pytest.mark.asyncio
async def test_non_member_forbidden(client: AsyncClient) -> None:
    owner_token = await _signup(client, "owner3@example.com", "Owner")
    outsider_token = await _signup(client, "outsider@example.com", "Outsider")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    create = await client.post(
        "/api/v1/organizations",
        headers=owner_headers,
        json={"name": "Private Team"},
    )
    org_id = create.json()["id"]

    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}
    response = await client.get(f"/api/v1/organizations/{org_id}", headers=outsider_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_org_document_upload_and_list(client: AsyncClient) -> None:
    owner_token = await _signup(client, "owner4@example.com", "Owner")
    headers = {"Authorization": f"Bearer {owner_token}"}

    create = await client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Docs Team"},
    )
    org_id = create.json()["id"]

    upload = await client.post(
        "/api/v1/documents/upload",
        headers=headers,
        params={"organization_id": org_id},
        files={"files": ("team-notes.txt", b"shared policy text", "text/plain")},
    )
    assert upload.status_code == 201
    assert upload.json()[0]["scope"] == "organization"

    listing = await client.get(
        "/api/v1/documents",
        headers=headers,
        params={"organization_id": org_id},
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


@pytest.mark.asyncio
async def test_only_owner_can_delete_organization(client: AsyncClient) -> None:
    owner_token = await _signup(client, "owner5@example.com", "Owner")
    member_token = await _signup(client, "member5@example.com", "Member")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    create = await client.post(
        "/api/v1/organizations",
        headers=owner_headers,
        json={"name": "Delete Me"},
    )
    org_id = create.json()["id"]

    await client.post(
        f"/api/v1/organizations/{org_id}/members",
        headers=owner_headers,
        json={"email": "member5@example.com", "role": "member"},
    )

    member_headers = {"Authorization": f"Bearer {member_token}"}
    denied = await client.delete(f"/api/v1/organizations/{org_id}", headers=member_headers)
    assert denied.status_code == 403

    allowed = await client.delete(f"/api/v1/organizations/{org_id}", headers=owner_headers)
    assert allowed.status_code == 200
