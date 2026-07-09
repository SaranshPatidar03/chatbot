"""User settings repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.settings import UserSettings
from app.db.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[UserSettings]):
    model = UserSettings

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_for_user(self, user_id: str) -> UserSettings | None:
        stmt = select(UserSettings).where(UserSettings.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: str) -> UserSettings:
        existing = await self.get_for_user(user_id)
        if existing:
            return existing
        settings = UserSettings(user_id=user_id)
        return await self.add(settings)
