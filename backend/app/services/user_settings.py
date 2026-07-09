"""Per-user LLM and RAG preference use cases."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.core.deps import UnitOfWork
from app.db.models.settings import UserSettings
from app.db.models.user import User
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdateRequest


class UserSettingsService:
    """Read and update user-specific model / RAG preferences."""

    def __init__(self, uow: UnitOfWork, settings: Settings | None = None) -> None:
        self.uow = uow
        self.settings = settings or get_settings()

    async def get_settings(self, user: User) -> UserSettingsResponse:
        record = await self.uow.settings.get_or_create(user.id)
        return UserSettingsResponse.model_validate(record)

    async def update_settings(
        self,
        user: User,
        payload: UserSettingsUpdateRequest,
    ) -> UserSettingsResponse:
        record = await self.uow.settings.get_or_create(user.id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return UserSettingsResponse.model_validate(record)

        if updates.get("allow_general_knowledge") and not self.settings.rag_allow_general_knowledge:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="General knowledge is disabled by platform policy.",
            )

        for field, value in updates.items():
            setattr(record, field, value)

        await self.uow.session.flush()
        await self.uow.session.refresh(record)
        return UserSettingsResponse.model_validate(record)
