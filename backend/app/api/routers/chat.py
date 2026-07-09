"""Chat API routes with SSE streaming."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.api.auth_deps import get_current_user
from app.core.deps import UnitOfWork, get_uow
from app.db.models.user import User
from app.schemas.chat import (
    ChatCreateRequest,
    ChatListResponse,
    ChatResponse,
    ChatUpdateRequest,
    ChatExportResponse,
    ChatImportRequest,
    ChatSearchResponse,
    MessageDeleteResponse,
    MessageListResponse,
    MessageResponse,
    SendMessageRequest,
    CitationItem,
)
from app.services.chat import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


def _chat_response(chat) -> ChatResponse:
    return ChatResponse.model_validate(chat)


def _message_response(message) -> MessageResponse:
    citations = [CitationItem.model_validate(item) for item in (message.citations or [])]
    return MessageResponse(
        id=message.id,
        chat_id=message.chat_id,
        role=message.role,
        content=message.content,
        citations=citations,
        latency_ms=message.latency_ms,
        model_provider=message.model_provider,
        model_name=message.model_name,
        created_at=message.created_at,
    )


@router.get("/search", response_model=ChatSearchResponse)
async def search_chats(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ChatSearchResponse:
    items = await ChatService(uow).search_chats(current_user, q, limit=limit)
    return ChatSearchResponse(
        items=[_chat_response(chat) for chat in items],
        total=len(items),
    )


@router.get("", response_model=ChatListResponse)
async def list_chats(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ChatListResponse:
    items, total = await ChatService(uow).list_chats(current_user, page=page, page_size=page_size)
    return ChatListResponse(items=[_chat_response(chat) for chat in items], total=total)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    payload: ChatCreateRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ChatResponse:
    chat = await ChatService(uow).create_chat(
        current_user,
        title=payload.title,
        organization_id=payload.organization_id,
    )
    return _chat_response(chat)


@router.patch("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    payload: ChatUpdateRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ChatResponse:
    chat = await ChatService(uow).update_chat(
        current_user,
        chat_id,
        title=payload.title,
        is_pinned=payload.is_pinned,
        is_archived=payload.is_archived,
    )
    return _chat_response(chat)


@router.delete("/{chat_id}", response_model=MessageDeleteResponse)
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MessageDeleteResponse:
    await ChatService(uow).delete_chat(current_user, chat_id)
    return MessageDeleteResponse(message="Chat deleted.")


@router.get("/{chat_id}/export", response_model=ChatExportResponse)
async def export_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ChatExportResponse:
    chat, messages = await ChatService(uow).export_chat(current_user, chat_id)
    return ChatExportResponse(
        chat=_chat_response(chat),
        messages=[_message_response(message) for message in messages],
    )


@router.post("/import", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def import_chat(
    payload: ChatImportRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> ChatResponse:
    chat = await ChatService(uow).import_chat(
        current_user,
        title=payload.title,
        messages=payload.messages,
        organization_id=payload.organization_id,
    )
    return _chat_response(chat)


@router.get("/{chat_id}/messages", response_model=MessageListResponse)
async def list_messages(
    chat_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> MessageListResponse:
    items, total = await ChatService(uow).list_messages(
        current_user,
        chat_id,
        page=page,
        page_size=page_size,
    )
    return MessageListResponse(items=[_message_response(message) for message in items], total=total)


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> StreamingResponse:
    service = ChatService(uow)

    async def event_stream():
        async for frame in service.stream_message(current_user, chat_id, payload.content):
            yield frame

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{chat_id}/messages/{message_id}/regenerate")
async def regenerate_message(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> StreamingResponse:
    service = ChatService(uow)

    async def event_stream():
        async for frame in service.stream_regenerate(current_user, chat_id, message_id):
            yield frame

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
