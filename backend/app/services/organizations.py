"""Organization workspace use cases."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.deps import UnitOfWork
from app.db.enums import OrgRole
from app.db.models.organization import Organization, OrganizationMember
from app.db.models.user import User
from app.embeddings.store import VectorStore
from app.schemas.organizations import (
    OrganizationCreateRequest,
    OrganizationDetail,
    OrganizationListResponse,
    OrganizationMemberAddRequest,
    OrganizationMemberItem,
    OrganizationMemberListResponse,
    OrganizationMemberUpdateRequest,
    OrganizationSummary,
    OrganizationUpdateRequest,
)
from app.utils.slug import slugify


class OrganizationService:
    """CRUD and membership management for shared workspaces."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def list_for_user(self, user: User) -> OrganizationListResponse:
        orgs = await self.uow.organizations.list_for_user(user.id)
        items: list[OrganizationSummary] = []
        for org in orgs:
            membership = await self.uow.organizations.get_membership(org.id, user.id)
            items.append(
                OrganizationSummary(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    description=org.description,
                    created_at=org.created_at,
                    my_role=membership.role if membership else None,
                )
            )
        return OrganizationListResponse(items=items, total=len(items))

    async def create(self, user: User, payload: OrganizationCreateRequest) -> OrganizationDetail:
        slug = await self._unique_slug(payload.slug or slugify(payload.name))
        organization = Organization(
            name=payload.name.strip(),
            slug=slug,
            description=payload.description,
            created_by_id=user.id,
        )
        organization = await self.uow.organizations.add(organization)
        await self.uow.organizations.add_member(
            OrganizationMember(
                organization_id=organization.id,
                user_id=user.id,
                role=OrgRole.OWNER.value,
            )
        )
        await self.uow.audit_logs.record(
            actor_id=user.id,
            action="organization.create",
            resource_type="organization",
            resource_id=organization.id,
        )
        return await self.get_detail(user, organization.id)

    async def get_detail(self, user: User, org_id: str) -> OrganizationDetail:
        organization, membership = await self._require_member(user, org_id)
        return OrganizationDetail(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            description=organization.description,
            created_at=organization.created_at,
            my_role=membership.role,
            member_count=await self.uow.organizations.count_members(org_id),
            created_by_id=organization.created_by_id,
        )

    async def update(
        self,
        user: User,
        org_id: str,
        payload: OrganizationUpdateRequest,
    ) -> OrganizationDetail:
        organization, membership = await self._require_member(user, org_id)
        if not self.uow.organizations.can_manage_members(membership.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

        if payload.name is not None:
            organization.name = payload.name.strip()
        if payload.description is not None:
            organization.description = payload.description
        await self.uow.session.flush()
        await self.uow.audit_logs.record(
            actor_id=user.id,
            action="organization.update",
            resource_type="organization",
            resource_id=organization.id,
        )
        return await self.get_detail(user, org_id)

    async def delete(self, user: User, org_id: str) -> None:
        organization, membership = await self._require_member(user, org_id)
        if membership.role != OrgRole.OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can delete organizations.")

        documents = await self.uow.documents.list_for_organization(org_id, limit=10_000)
        store = VectorStore()
        for document in documents:
            store.delete_document_vectors(document)
        store.delete_collection(VectorStore.org_collection_name(org_id))

        await self.uow.session.delete(organization)
        await self.uow.session.flush()
        await self.uow.audit_logs.record(
            actor_id=user.id,
            action="organization.delete",
            resource_type="organization",
            resource_id=org_id,
        )

    async def list_members(self, user: User, org_id: str) -> OrganizationMemberListResponse:
        await self._require_member(user, org_id)
        members = await self.uow.organizations.list_members(org_id)
        items = [
            OrganizationMemberItem(
                user_id=member.user_id,
                email=member.user.email,
                full_name=member.user.full_name,
                role=member.role,
                joined_at=member.created_at,
            )
            for member in members
            if member.user is not None
        ]
        return OrganizationMemberListResponse(items=items, total=len(items))

    async def add_member(
        self,
        actor: User,
        org_id: str,
        payload: OrganizationMemberAddRequest,
    ) -> OrganizationMemberItem:
        _, membership = await self._require_member(actor, org_id)
        if not self.uow.organizations.can_manage_members(membership.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

        invitee = await self.uow.users.get_by_email(str(payload.email))
        if invitee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No user found with that email. They must sign up first.",
            )

        existing = await self.uow.organizations.get_membership(org_id, invitee.id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member.")

        member = await self.uow.organizations.add_member(
            OrganizationMember(
                organization_id=org_id,
                user_id=invitee.id,
                role=payload.role,
            )
        )
        await self.uow.session.refresh(member, attribute_names=["user"])
        await self.uow.audit_logs.record(
            actor_id=actor.id,
            action="organization.member.add",
            resource_type="organization",
            resource_id=org_id,
            details={"user_id": invitee.id, "role": payload.role},
        )
        return OrganizationMemberItem(
            user_id=member.user_id,
            email=invitee.email,
            full_name=invitee.full_name,
            role=member.role,
            joined_at=member.created_at,
        )

    async def update_member(
        self,
        actor: User,
        org_id: str,
        user_id: str,
        payload: OrganizationMemberUpdateRequest,
    ) -> OrganizationMemberItem:
        _, actor_membership = await self._require_member(actor, org_id)
        if not self.uow.organizations.can_manage_members(actor_membership.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
        if actor_membership.role != OrgRole.OWNER.value and payload.role == OrgRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can assign the owner role.",
            )

        target = await self.uow.organizations.get_membership(org_id, user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

        if target.role == OrgRole.OWNER.value and payload.role != OrgRole.OWNER.value:
            owners = await self.uow.organizations.count_role(org_id, OrgRole.OWNER.value)
            if owners <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot demote the last owner.",
                )

        target.role = payload.role
        await self.uow.session.flush()
        user = await self.uow.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
        return OrganizationMemberItem(
            user_id=target.user_id,
            email=user.email,
            full_name=user.full_name,
            role=target.role,
            joined_at=target.created_at,
        )

    async def remove_member(self, actor: User, org_id: str, user_id: str) -> None:
        _, actor_membership = await self._require_member(actor, org_id)
        target = await self.uow.organizations.get_membership(org_id, user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

        is_self = actor.id == user_id
        if not is_self and not self.uow.organizations.can_manage_members(actor_membership.role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
        if target.role == OrgRole.OWNER.value:
            owners = await self.uow.organizations.count_role(org_id, OrgRole.OWNER.value)
            if owners <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last owner.",
                )

        await self.uow.organizations.remove_member(target)
        await self.uow.audit_logs.record(
            actor_id=actor.id,
            action="organization.member.remove",
            resource_type="organization",
            resource_id=org_id,
            details={"user_id": user_id},
        )

    async def _require_member(
        self,
        user: User,
        org_id: str,
    ) -> tuple[Organization, OrganizationMember]:
        organization = await self.uow.organizations.get_by_id(org_id)
        if organization is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
        membership = await self.uow.organizations.get_membership(org_id, user.id)
        if membership is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization.")
        return organization, membership

    async def _unique_slug(self, base_slug: str) -> str:
        slug = slugify(base_slug)
        candidate = slug
        suffix = 1
        while await self.uow.organizations.get_by_slug(candidate) is not None:
            candidate = f"{slug}-{suffix}"
            suffix += 1
        return candidate

    async def require_membership(self, user: User, org_id: str) -> OrganizationMember:
        """Public helper for other services."""
        _, membership = await self._require_member(user, org_id)
        return membership

    async def can_manage_document(self, user: User, document) -> bool:
        if document.organization_id:
            membership = await self.uow.organizations.get_membership(document.organization_id, user.id)
            return membership is not None and self.uow.organizations.can_manage_members(membership.role)
        return document.owner_id == user.id
