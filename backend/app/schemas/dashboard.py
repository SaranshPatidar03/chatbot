"""Pydantic schemas for dashboard summary."""

from datetime import datetime

from pydantic import BaseModel


class DashboardDocumentItem(BaseModel):
    id: str
    title: str
    status: str
    file_size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardChatItem(BaseModel):
    id: str
    title: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardSummaryResponse(BaseModel):
    document_count: int
    chat_count: int
    storage_bytes: int
    documents_processing: int
    recent_documents: list[DashboardDocumentItem]
    recent_chats: list[DashboardChatItem]
