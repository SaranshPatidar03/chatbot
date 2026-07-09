"""Platform admin API routes."""

from fastapi import APIRouter, Depends, Query, status

from app.api.auth_deps import require_platform_admin
from app.core.deps import UnitOfWork, get_uow
from app.db.models.user import User
from app.schemas.admin import (
    AdminAnalyticsEventListResponse,
    AdminAnalyticsSummary,
    AdminAuditLogListResponse,
    AdminDocumentListResponse,
    AdminMessageResponse,
    AdminStorageSummary,
    AdminSystemConfig,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserUpdateRequest,
)
from app.schemas.health import ReadinessResponse
from app.services.admin import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminUserListResponse:
    return await AdminService(uow).list_users(
        page=page,
        page_size=page_size,
        query=q,
        role=role,
        is_active=is_active,
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user(
    user_id: str,
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminUserDetail:
    return await AdminService(uow).get_user(user_id)


@router.patch("/users/{user_id}", response_model=AdminUserDetail)
async def update_user(
    user_id: str,
    payload: AdminUserUpdateRequest,
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminUserDetail:
    return await AdminService(uow).update_user(admin, user_id, payload)


@router.get("/documents", response_model=AdminDocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminDocumentListResponse:
    return await AdminService(uow).list_documents(
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )


@router.get("/storage/summary", response_model=AdminStorageSummary)
async def storage_summary(
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminStorageSummary:
    return await AdminService(uow).storage_summary()


@router.delete("/documents/{document_id}", response_model=AdminMessageResponse)
async def delete_document(
    document_id: str,
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminMessageResponse:
    await AdminService(uow).delete_document(admin, document_id)
    return AdminMessageResponse(message="Document deleted.")


@router.get("/audit-logs", response_model=AdminAuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = Query(None),
    actor_id: str | None = Query(None),
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminAuditLogListResponse:
    return await AdminService(uow).list_audit_logs(
        page=page,
        page_size=page_size,
        action=action,
        actor_id=actor_id,
    )


@router.get("/analytics/summary", response_model=AdminAnalyticsSummary)
async def analytics_summary(
    days: int = Query(7, ge=1, le=90),
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminAnalyticsSummary:
    return await AdminService(uow).analytics_summary(days=days)


@router.get("/analytics/events", response_model=AdminAnalyticsEventListResponse)
async def list_analytics_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    event_type: str | None = Query(None),
    user_id: str | None = Query(None),
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminAnalyticsEventListResponse:
    return await AdminService(uow).list_analytics_events(
        page=page,
        page_size=page_size,
        event_type=event_type,
        user_id=user_id,
    )


@router.get("/system/health", response_model=ReadinessResponse)
async def system_health(
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> ReadinessResponse:
    return await AdminService(uow).system_health()


@router.get("/system/config", response_model=AdminSystemConfig)
async def system_config(
    admin: User = Depends(require_platform_admin),
    uow: UnitOfWork = Depends(get_uow),
) -> AdminSystemConfig:
    return AdminService(uow).system_config()
