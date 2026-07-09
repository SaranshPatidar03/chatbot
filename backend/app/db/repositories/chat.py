"""Chat and message repositories."""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.chat import Chat, Message
from app.db.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    model = Chat

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_with_messages(self, chat_id: str) -> Chat | None:
        stmt = (
            select(Chat)
            .where(Chat.id == chat_id)
            .options(selectinload(Chat.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: str,
        *,
        include_archived: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Chat]:
        stmt: Select[tuple[Chat]] = select(Chat).where(Chat.user_id == user_id)
        if not include_archived:
            stmt = stmt.where(Chat.is_archived.is_(False))
        stmt = (
            stmt.order_by(Chat.is_pinned.desc(), Chat.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_for_user(self, user_id: str, query: str, *, limit: int = 20) -> list[Chat]:
        pattern = f"%{query.strip()}%"
        stmt = (
            select(Chat)
            .where(Chat.user_id == user_id, Chat.title.ilike(pattern))
            .order_by(Chat.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: str) -> int:
        stmt = select(func.count()).select_from(Chat).where(Chat.user_id == user_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())


class MessageRepository(BaseRepository[Message]):
    model = Message

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_for_chat(
        self,
        chat_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_in_user_chats(self, user_id: str, query: str, *, limit: int = 20) -> list[Message]:
        pattern = f"%{query.strip()}%"
        stmt = (
            select(Message)
            .join(Chat, Chat.id == Message.chat_id)
            .where(Chat.user_id == user_id, Message.content.ilike(pattern))
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
