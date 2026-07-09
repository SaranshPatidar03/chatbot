"""User repository."""

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.user import User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_settings(self, user_id: str) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.settings))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        return await self.get_by_email(email) is not None

    def _admin_filter_stmt(
        self,
        stmt: Select,
        *,
        query: str | None,
        role: str | None,
        is_active: bool | None,
    ) -> Select:
        if query:
            pattern = f"%{query.strip()}%"
            stmt = stmt.where(
                or_(User.email.ilike(pattern), User.full_name.ilike(pattern)),
            )
        if role:
            stmt = stmt.where(User.role == role)
        if is_active is not None:
            stmt = stmt.where(User.is_active.is_(is_active))
        return stmt

    async def list_admin(
        self,
        *,
        query: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[User]:
        stmt: Select[tuple[User]] = select(User)
        stmt = self._admin_filter_stmt(stmt, query=query, role=role, is_active=is_active)
        stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_admin(
        self,
        *,
        query: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(User)
        stmt = self._admin_filter_stmt(stmt, query=query, role=role, is_active=is_active)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
