"""Organization repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import OrgRole
from app.db.models.organization import Organization, OrganizationMember
from app.db.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_slug(self, slug: str) -> Organization | None:
        stmt = select(Organization).where(Organization.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_members(self, org_id: str) -> Organization | None:
        stmt = (
            select(Organization)
            .where(Organization.id == org_id)
            .options(selectinload(Organization.members))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_membership(self, org_id: str, user_id: str) -> OrganizationMember | None:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def membership_org_ids_for_user(self, user_id: str, org_ids: list[str]) -> set[str]:
        if not org_ids:
            return set()
        stmt = select(OrganizationMember.organization_id).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id.in_(org_ids),
        )
        result = await self.session.execute(stmt)
        return {str(row[0]) for row in result.all()}

    async def list_for_user(self, user_id: str) -> list[Organization]:
        stmt = (
            select(Organization)
            .join(OrganizationMember)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def list_members(self, org_id: str) -> list[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
            .options(selectinload(OrganizationMember.user))
            .order_by(OrganizationMember.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_members(self, org_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def count_role(self, org_id: str, role: str) -> int:
        stmt = (
            select(func.count())
            .select_from(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.role == role,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def remove_member(self, member: OrganizationMember) -> None:
        await self.session.delete(member)
        await self.session.flush()

    async def add_member(self, member: OrganizationMember) -> OrganizationMember:
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    def can_manage_members(self, role: str) -> bool:
        return role in {OrgRole.OWNER.value, OrgRole.ADMIN.value}
