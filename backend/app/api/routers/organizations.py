"""Organization API routes."""

from fastapi import APIRouter, Depends, status

from app.api.auth_deps import get_current_user
from app.core.deps import UnitOfWork, get_uow
from app.db.models.user import User
from app.schemas.organizations import (
    MessageResponse,
    OrganizationCreateRequest,
    OrganizationDetail,
    OrganizationListResponse,
    OrganizationMemberAddRequest,
    OrganizationMemberItem,
    OrganizationMemberListResponse,
    OrganizationMemberUpdateRequest,
    OrganizationUpdateRequest,
)
from app.services.organizations import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrganizationListResponse:
    return await OrganizationService(uow).list_for_user(current_user)


@router.post("", response_model=OrganizationDetail, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrganizationDetail:
    return await OrganizationService(uow).create(current_user, payload)


@router.get("/{org_id}", response_model=OrganizationDetail)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrganizationDetail:
    return await OrganizationService(uow).get_detail(current_user, org_id)


@router.patch("/{org_id}", response_model=OrganizationDetail)
async def update_organization(
    org_id: str,
    payload: OrganizationUpdateRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrganizationDetail:
    return await OrganizationService(uow).update(current_user, org_id, payload)


@router.delete("/{org_id}", response_model=MessageResponse)
async def delete_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MessageResponse:
    await OrganizationService(uow).delete(current_user, org_id)
    return MessageResponse(message="Organization deleted.")


@router.get("/{org_id}/members", response_model=OrganizationMemberListResponse)
async def list_members(
    org_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrganizationMemberListResponse:
    return await OrganizationService(uow).list_members(current_user, org_id)


@router.post(
    "/{org_id}/members",
    response_model=OrganizationMemberItem,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    org_id: str,
    payload: OrganizationMemberAddRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrganizationMemberItem:
    return await OrganizationService(uow).add_member(current_user, org_id, payload)


@router.patch("/{org_id}/members/{user_id}", response_model=OrganizationMemberItem)
async def update_member(
    org_id: str,
    user_id: str,
    payload: OrganizationMemberUpdateRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> OrganizationMemberItem:
    return await OrganizationService(uow).update_member(current_user, org_id, user_id, payload)


@router.delete("/{org_id}/members/{user_id}", response_model=MessageResponse)
async def remove_member(
    org_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MessageResponse:
    await OrganizationService(uow).remove_member(current_user, org_id, user_id)
    return MessageResponse(message="Member removed.")
