"""Session and password-reset repositories."""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.session import PasswordResetToken, UserSession
from app.db.repositories.base import BaseRepository


class SessionRepository(BaseRepository[UserSession]):
    model = UserSession

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        stmt = select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_for_user(self, user_id: str) -> list[UserSession]:
        now = datetime.now(UTC)
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_revoked.is_(False),
            UserSession.expires_at > now,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def revoke(self, session_row: UserSession) -> UserSession:
        session_row.is_revoked = True
        session_row.revoked_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(session_row)
        return session_row

    async def revoke_all_for_user(self, user_id: str) -> int:
        now = datetime.now(UTC)
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_revoked.is_(False))
            .values(is_revoked=True, revoked_at=now)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return int(result.rowcount or 0)


class PasswordResetRepository(BaseRepository[PasswordResetToken]):
    model = PasswordResetToken

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(self, token: PasswordResetToken) -> PasswordResetToken:
        token.used_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(token)
        return token
