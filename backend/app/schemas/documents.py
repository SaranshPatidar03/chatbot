"""Pydantic schemas for document APIs."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class DocumentResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    content_type: str | None
    extension: str | None
    file_size_bytes: int
    content_hash: str
    scope: str
    status: str
    version: int
    page_count: int | None
    chunk_count: int
    source_url: str | None
    error_message: str | None
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    meta: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class DocumentChunkResponse(BaseModel):
    id: str
    chunk_index: int
    content: str
    page_number: int | None
    token_count: int | None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentContentResponse(BaseModel):
    document_id: str
    text: str
    page_count: int | None
    chunk_count: int


class UrlIngestRequest(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=512)


class MessageResponse(BaseModel):
    message: str
