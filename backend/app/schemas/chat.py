"""Pydantic schemas for chat APIs."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    content_preview: str
    page_number: int | None
    chunk_index: int
    score: float
    citation: str


class ChatCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    organization_id: str | None = None


class ChatUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    is_pinned: bool | None = None
    is_archived: bool | None = None


class ChatResponse(BaseModel):
    id: str
    title: str
    is_pinned: bool
    is_archived: bool
    organization_id: str | None
    model_provider: str | None
    model_name: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    items: list[ChatResponse]
    total: int


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    role: str
    content: str
    citations: list[CitationItem] = Field(default_factory=list)
    latency_ms: float | None
    model_provider: str | None
    model_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class MessageDeleteResponse(BaseModel):
    message: str


class ChatExportResponse(BaseModel):
    version: int = 1
    chat: ChatResponse
    messages: list[MessageResponse]


class ChatImportRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    organization_id: str | None = None


class ChatSearchResponse(BaseModel):
    items: list[ChatResponse]
    total: int
