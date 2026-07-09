"""Dashboard summary use cases."""

from __future__ import annotations

from sqlalchemy import func, select

from app.core.deps import UnitOfWork
from app.db.enums import DocumentStatus
from app.db.models.document import Document
from app.db.models.user import User
from app.schemas.dashboard import (
    DashboardChatItem,
    DashboardDocumentItem,
    DashboardSummaryResponse,
)


class DashboardService:
    """Aggregate counts and recent activity for the signed-in user."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def summary(self, user: User) -> DashboardSummaryResponse:
        document_count = await self.uow.documents.count_for_owner(user.id)
        storage_bytes = await self.uow.documents.total_storage_bytes(user.id)
        chat_count = await self.uow.chats.count_for_user(user.id)
        documents_processing = await self._count_processing(user.id)

        recent_documents = await self.uow.documents.list_for_owner(
            user.id,
            offset=0,
            limit=5,
        )
        recent_chats = await self.uow.chats.list_for_user(user.id, offset=0, limit=5)

        return DashboardSummaryResponse(
            document_count=document_count,
            chat_count=chat_count,
            storage_bytes=storage_bytes,
            documents_processing=documents_processing,
            recent_documents=[
                DashboardDocumentItem.model_validate(doc) for doc in recent_documents
            ],
            recent_chats=[DashboardChatItem.model_validate(chat) for chat in recent_chats],
        )

    async def _count_processing(self, owner_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Document)
            .where(
                Document.owner_id == owner_id,
                Document.status.in_(
                    [
                        DocumentStatus.PENDING.value,
                        DocumentStatus.PROCESSING.value,
                    ]
                ),
            )
        )
        result = await self.uow.session.execute(stmt)
        return int(result.scalar_one())
