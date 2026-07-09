"""Grounded chat use cases with streaming responses."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.core.deps import UnitOfWork
from app.core.logging import get_logger
from app.db.enums import AnalyticsEventType, MessageRole
from app.db.models.chat import Chat, Message
from app.db.models.user import User
from app.llm.factory import ProviderName, get_llm_provider
from app.llm.protocol import ChatMessage
from app.rag.citations import chunk_to_citation_dict
from app.rag.prompts import build_grounded_messages
from app.services.knowledge_retrieval import KnowledgeRetrieval

logger = get_logger(__name__)


class ChatService:
    """Chat CRUD and grounded streaming message generation."""

    def __init__(self, uow: UnitOfWork, settings: Settings | None = None) -> None:
        self.uow = uow
        self.settings = settings or get_settings()

    async def list_chats(self, user: User, *, page: int = 1, page_size: int = 50) -> tuple[list[Chat], int]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size
        items = await self.uow.chats.list_for_user(user.id, offset=offset, limit=page_size)
        total = await self.uow.chats.count_for_user(user.id)
        return items, total

    async def create_chat(
        self,
        user: User,
        *,
        title: str | None = None,
        organization_id: str | None = None,
    ) -> Chat:
        if organization_id:
            membership = await self.uow.organizations.get_membership(organization_id, user.id)
            if membership is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a member of this organization.",
                )

        chat = Chat(
            user_id=user.id,
            organization_id=organization_id,
            title=title or "New chat",
        )
        return await self.uow.chats.add(chat)

    async def update_chat(self, user: User, chat_id: str, **updates) -> Chat:
        chat = await self._get_owned_chat(user, chat_id)
        if updates.get("title") is not None:
            chat.title = updates["title"]
        if updates.get("is_pinned") is not None:
            chat.is_pinned = updates["is_pinned"]
        if updates.get("is_archived") is not None:
            chat.is_archived = updates["is_archived"]
        await self.uow.session.flush()
        await self.uow.session.refresh(chat)
        return chat

    async def delete_chat(self, user: User, chat_id: str) -> None:
        chat = await self._get_owned_chat(user, chat_id)
        await self.uow.chats.delete(chat)

    async def search_chats(self, user: User, query: str, *, limit: int = 20) -> list[Chat]:
        return await self.uow.chats.search_for_user(user.id, query, limit=limit)

    async def export_chat(self, user: User, chat_id: str) -> tuple[Chat, list[Message]]:
        chat = await self._get_owned_chat(user, chat_id)
        messages, _ = await self.list_messages(user, chat_id, page=1, page_size=500)
        return chat, messages

    async def import_chat(
        self,
        user: User,
        *,
        title: str | None,
        messages: list[dict],
        organization_id: str | None = None,
    ) -> Chat:
        chat = await self.create_chat(
            user,
            title=title or "Imported chat",
            organization_id=organization_id,
        )
        for item in messages:
            role = str(item.get("role", "user"))
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            if role not in {MessageRole.USER.value, MessageRole.ASSISTANT.value}:
                continue
            message = Message(
                chat_id=chat.id,
                role=role,
                content=content,
                citations=item.get("citations") if role == MessageRole.ASSISTANT.value else None,
            )
            await self.uow.messages.add(message)
        await self.uow.session.flush()
        await self.uow.session.refresh(chat)
        return chat

    async def list_messages(
        self,
        user: User,
        chat_id: str,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[Message], int]:
        await self._get_owned_chat(user, chat_id)
        page = max(page, 1)
        page_size = min(max(page_size, 1), 200)
        offset = (page - 1) * page_size
        items = await self.uow.messages.list_for_chat(chat_id, offset=offset, limit=page_size)
        return items, len(items)

    async def stream_message(
        self,
        user: User,
        chat_id: str,
        content: str,
    ) -> AsyncIterator[str]:
        """Yield SSE frames for a new user turn."""
        chat = await self._get_owned_chat(user, chat_id)
        user_message = Message(chat_id=chat.id, role=MessageRole.USER.value, content=content)
        user_message = await self.uow.messages.add(user_message)
        await self._maybe_update_title(chat, content)
        await self.uow.session.flush()

        yield self._sse("start", {"user_message_id": user_message.id})

        history = await self._history_messages(chat.id, exclude_id=user_message.id)
        async for frame in self._stream_assistant_turn(user, chat, content, history):
            yield frame

    async def stream_regenerate(
        self,
        user: User,
        chat_id: str,
        message_id: str,
    ) -> AsyncIterator[str]:
        """Regenerate an assistant message in place."""
        chat = await self._get_owned_chat(user, chat_id)
        assistant_message = await self.uow.messages.get_by_id(message_id)
        if (
            not assistant_message
            or assistant_message.chat_id != chat.id
            or assistant_message.role != MessageRole.ASSISTANT.value
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")

        messages = await self.uow.messages.list_for_chat(chat.id, limit=500)
        user_content = self._find_preceding_user_content(messages, assistant_message.id)
        if not user_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot regenerate without a preceding user message.",
            )

        await self.uow.messages.delete(assistant_message)
        await self.uow.session.flush()

        history = await self._history_messages(chat.id)
        async for frame in self._stream_assistant_turn(user, chat, user_content, history):
            yield frame

    async def _stream_assistant_turn(
        self,
        user: User,
        chat: Chat,
        question: str,
        history: list[ChatMessage],
    ) -> AsyncIterator[str]:
        started = time.perf_counter()
        chunks, _, _, has_context = await KnowledgeRetrieval(self.uow, self.settings).retrieve(
            user,
            question,
        )
        citations = [chunk_to_citation_dict(chunk) for chunk in chunks]
        yield self._sse("citations", {"citations": citations})

        user_settings = await self.uow.settings.get_for_user(user.id)
        allow_general = (
            user_settings.allow_general_knowledge
            if user_settings
            else self.settings.rag_allow_general_knowledge
        )
        system_prompt = user_settings.system_prompt if user_settings else None
        temperature = user_settings.temperature if user_settings else 0.2
        top_p = user_settings.top_p if user_settings else 1.0
        max_tokens = user_settings.max_tokens if user_settings else 1024

        provider_name: ProviderName = (
            user_settings.llm_provider  # type: ignore[assignment]
            if user_settings
            else self.settings.default_llm_provider
        )
        model_name = (
            user_settings.llm_model
            if user_settings
            else (
                self.settings.openai_default_model
                if provider_name == "openai"
                else self.settings.ollama_default_model
            )
        )
        provider = get_llm_provider(provider_name, settings=self.settings)

        if not has_context:
            content = self.settings.grounded_refusal_message
            yield self._sse("token", {"content": content})
            assistant = await self._save_assistant_message(
                chat=chat,
                content=content,
                citations=[],
                provider_name=provider_name,
                model_name=model_name,
                latency_ms=(time.perf_counter() - started) * 1000,
            )
            yield self._sse("done", {"message_id": assistant.id, "latency_ms": assistant.latency_ms})
            return

        grounded_messages = build_grounded_messages(
            question=question,
            context_blocks=[chunk.to_context_block() for chunk in chunks],
            history=history,
            system_prompt=system_prompt,
            allow_general_knowledge=allow_general,
        )

        full_content = ""
        async for chunk in provider.stream(
            grounded_messages,
            model=model_name,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        ):
            if chunk.content:
                full_content += chunk.content
                yield self._sse("token", {"content": chunk.content})

        latency_ms = (time.perf_counter() - started) * 1000
        assistant = await self._save_assistant_message(
            chat=chat,
            content=full_content.strip() or self.settings.grounded_refusal_message,
            citations=citations,
            provider_name=provider_name,
            model_name=model_name,
            latency_ms=latency_ms,
        )

        await self.uow.analytics.record(
            user_id=user.id,
            event_type=AnalyticsEventType.LLM_CALL.value,
            name="chat_completion",
            duration_ms=latency_ms,
            status="success",
            meta={"chat_id": chat.id, "message_id": assistant.id, "citations": len(citations)},
        )
        await self.uow.analytics.record(
            user_id=user.id,
            event_type=AnalyticsEventType.RETRIEVAL.value,
            name="chat_retrieval",
            status="success",
            meta={"chat_id": chat.id, "chunks": len(chunks)},
        )

        yield self._sse("done", {"message_id": assistant.id, "latency_ms": round(latency_ms, 2)})

    async def _save_assistant_message(
        self,
        *,
        chat: Chat,
        content: str,
        citations: list[dict],
        provider_name: str,
        model_name: str,
        latency_ms: float,
    ) -> Message:
        message = Message(
            chat_id=chat.id,
            role=MessageRole.ASSISTANT.value,
            content=content,
            citations=citations,
            latency_ms=latency_ms,
            model_provider=provider_name,
            model_name=model_name,
        )
        message = await self.uow.messages.add(message)
        chat.updated_at = datetime.now(UTC)
        await self.uow.session.flush()
        return message

    async def _history_messages(self, chat_id: str, *, exclude_id: str | None = None) -> list[ChatMessage]:
        messages = await self.uow.messages.list_for_chat(chat_id, limit=200)
        history: list[ChatMessage] = []
        for message in messages:
            if exclude_id and message.id == exclude_id:
                continue
            if message.role in {MessageRole.USER.value, MessageRole.ASSISTANT.value}:
                history.append(ChatMessage(role=message.role, content=message.content))
        return history[-12:]

    async def _maybe_update_title(self, chat: Chat, content: str) -> None:
        if chat.title != "New chat":
            return
        chat.title = content.strip()[:80] or "New chat"
        await self.uow.session.flush()

    async def _get_owned_chat(self, user: User, chat_id: str) -> Chat:
        chat = await self.uow.chats.get_by_id(chat_id)
        if not chat or chat.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
        return chat

    @staticmethod
    def _find_preceding_user_content(messages: list[Message], assistant_id: str) -> str | None:
        for index, message in enumerate(messages):
            if message.id != assistant_id:
                continue
            if index == 0:
                return None
            previous = messages[index - 1]
            if previous.role == MessageRole.USER.value:
                return previous.content
            return None
        return None

    @staticmethod
    def _sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
