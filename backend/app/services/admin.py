"""Platform administration use cases."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.core.deps import UnitOfWork
from app.core.logging import get_logger
from app.db.models.user import User
from app.schemas.admin import (
    AdminAnalyticsEventItem,
    AdminAnalyticsEventListResponse,
    AdminAnalyticsSummary,
    AdminAuditLogItem,
    AdminAuditLogListResponse,
    AdminDocumentListResponse,
    AdminDocumentSummary,
    AdminStorageSummary,
    AdminSystemConfig,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserSummary,
    AdminUserUpdateRequest,
)
from app.schemas.health import ReadinessResponse
from app.services.health import HealthService
from app.services.indexing import IndexService

logger = get_logger(__name__)


class AdminService:
    """Platform-wide administration operations."""

    def __init__(self, uow: UnitOfWork, settings: Settings | None = None) -> None:
        self.uow = uow
        self.settings = settings or get_settings()

    async def list_users(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        query: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> AdminUserListResponse:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size
        items = await self.uow.users.list_admin(
            query=query,
            role=role,
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )
        total = await self.uow.users.count_admin(query=query, role=role, is_active=is_active)
        return AdminUserListResponse(
            items=[AdminUserSummary.model_validate(user) for user in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user(self, user_id: str) -> AdminUserDetail:
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        summary = AdminUserSummary.model_validate(user)
        return AdminUserDetail(
            **summary.model_dump(),
            document_count=await self.uow.documents.count_for_owner(user.id),
            chat_count=await self.uow.chats.count_for_user(user.id),
        )

    async def update_user(
        self,
        actor: User,
        user_id: str,
        payload: AdminUserUpdateRequest,
    ) -> AdminUserDetail:
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if user.id == actor.id and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account.",
            )

        changes: dict[str, object] = {}
        if payload.role is not None and payload.role != user.role:
            changes["role"] = payload.role
            user.role = payload.role
        if payload.is_active is not None and payload.is_active != user.is_active:
            changes["is_active"] = payload.is_active
            user.is_active = payload.is_active
        if payload.is_verified is not None and payload.is_verified != user.is_verified:
            changes["is_verified"] = payload.is_verified
            user.is_verified = payload.is_verified

        if changes:
            await self.uow.session.flush()
            await self.uow.session.refresh(user)
            await self.uow.audit_logs.record(
                actor_id=actor.id,
                action="admin.user.update",
                resource_type="user",
                resource_id=user.id,
                details=changes,
            )
            logger.info("admin_user_updated", actor_id=actor.id, user_id=user.id, changes=changes)

        return await self.get_user(user.id)

    async def list_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
    ) -> AdminDocumentListResponse:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size
        items = await self.uow.documents.list_platform(
            status=status_filter,
            offset=offset,
            limit=page_size,
        )
        total = await self.uow.documents.count_platform(status=status_filter)
        return AdminDocumentListResponse(
            items=[AdminDocumentSummary.model_validate(doc) for doc in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def storage_summary(self) -> AdminStorageSummary:
        raw = await self.uow.documents.platform_storage_summary()
        by_status = raw.get("by_status", {})
        if not isinstance(by_status, dict):
            by_status = {}
        document_count = sum(int(v) for v in by_status.values())
        return AdminStorageSummary(
            total_bytes=int(raw.get("total_bytes", 0)),
            document_count=document_count,
            by_status={str(k): int(v) for k, v in by_status.items()},
        )

    async def delete_document(self, actor: User, document_id: str) -> None:
        document = await self.uow.documents.get_by_id(document_id)
        if not document or document.status == DocumentStatus.DELETED.value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        await IndexService(self.uow, self.settings).purge_document_vectors(document)
        document.status = DocumentStatus.DELETED.value
        await self.uow.session.flush()
        await self.uow.audit_logs.record(
            actor_id=actor.id,
            action="admin.document.delete",
            resource_type="document",
            resource_id=document.id,
            details={"owner_id": document.owner_id},
        )

    async def list_audit_logs(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        actor_id: str | None = None,
    ) -> AdminAuditLogListResponse:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 200)
        offset = (page - 1) * page_size
        items = await self.uow.audit_logs.list_filtered(
            action=action,
            actor_id=actor_id,
            offset=offset,
            limit=page_size,
        )
        total = await self.uow.audit_logs.count_filtered(action=action, actor_id=actor_id)
        return AdminAuditLogListResponse(
            items=[AdminAuditLogItem.model_validate(row) for row in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def analytics_summary(self, *, days: int = 7) -> AdminAnalyticsSummary:
        raw = await self.uow.analytics.summarize(days=days)
        return AdminAnalyticsSummary.model_validate(raw)

    async def list_analytics_events(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        event_type: str | None = None,
        user_id: str | None = None,
    ) -> AdminAnalyticsEventListResponse:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 200)
        offset = (page - 1) * page_size
        items = await self.uow.analytics.list_admin(
            event_type=event_type,
            user_id=user_id,
            offset=offset,
            limit=page_size,
        )
        total = await self.uow.analytics.count_admin(event_type=event_type, user_id=user_id)
        return AdminAnalyticsEventListResponse(
            items=[AdminAnalyticsEventItem.model_validate(row) for row in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def system_health(self) -> ReadinessResponse:
        return await HealthService(self.settings).readiness()

    def system_config(self) -> AdminSystemConfig:
        return AdminSystemConfig(
            app_name=self.settings.app_name,
            app_env=self.settings.app_env,
            default_llm_provider=self.settings.default_llm_provider,
            default_embedding_provider=self.settings.default_embedding_provider,
            rag_top_k=self.settings.rag_top_k,
            rag_similarity_threshold=self.settings.rag_similarity_threshold,
        )
