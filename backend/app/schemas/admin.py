"""Pydantic schemas for admin APIs."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class AdminUserSummary(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserDetail(AdminUserSummary):
    document_count: int = 0
    chat_count: int = 0


class AdminUserListResponse(BaseModel):
    items: list[AdminUserSummary]
    total: int
    page: int
    page_size: int


class AdminUserUpdateRequest(BaseModel):
    role: Literal["user", "platform_admin"] | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class AdminDocumentSummary(BaseModel):
    id: str
    owner_id: str
    title: str
    original_filename: str
    status: str
    file_size_bytes: int
    chunk_count: int
    scope: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminDocumentListResponse(BaseModel):
    items: list[AdminDocumentSummary]
    total: int
    page: int
    page_size: int


class AdminStorageSummary(BaseModel):
    total_bytes: int
    document_count: int
    by_status: dict[str, int]


class AdminAuditLogItem(BaseModel):
    id: str
    actor_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str | None
    details: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminAuditLogListResponse(BaseModel):
    items: list[AdminAuditLogItem]
    total: int
    page: int
    page_size: int


class AdminAnalyticsSummary(BaseModel):
    days: int
    total_events: int
    by_type: dict[str, int]
    llm_calls: int
    llm_avg_latency_ms: float
    llm_total_tokens: int


class AdminAnalyticsEventItem(BaseModel):
    id: str
    user_id: str | None
    event_type: str
    name: str
    duration_ms: float | None
    token_count: int | None
    status: str | None
    meta: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminAnalyticsEventListResponse(BaseModel):
    items: list[AdminAnalyticsEventItem]
    total: int
    page: int
    page_size: int


class AdminSystemConfig(BaseModel):
    app_name: str
    app_env: str
    default_llm_provider: str
    default_embedding_provider: str
    rag_top_k: int
    rag_similarity_threshold: float


class AdminMessageResponse(BaseModel):
    message: str
