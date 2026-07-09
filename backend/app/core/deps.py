"""Dependency injection helpers for FastAPI request handlers."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.repositories import (
    AnalyticsRepository,
    AuditLogRepository,
    ChatRepository,
    DocumentChunkRepository,
    DocumentRepository,
    MessageRepository,
    OrganizationRepository,
    PasswordResetRepository,
    SessionRepository,
    SettingsRepository,
    UserRepository,
)
from app.db.session import get_db_session
from app.embeddings.factory import get_embedding_provider
from app.embeddings.protocol import EmbeddingProvider
from app.embeddings.store import VectorStore
from app.llm.factory import get_llm_provider
from app.llm.protocol import LLMProvider


@dataclass(slots=True)
class UnitOfWork:
    """Request-scoped bundle of repositories sharing one DB session."""

    session: AsyncSession
    users: UserRepository
    organizations: OrganizationRepository
    sessions: SessionRepository
    password_resets: PasswordResetRepository
    documents: DocumentRepository
    chunks: DocumentChunkRepository
    chats: ChatRepository
    messages: MessageRepository
    settings: SettingsRepository
    audit_logs: AuditLogRepository
    analytics: AnalyticsRepository


def build_uow(session: AsyncSession) -> UnitOfWork:
    """Construct repositories bound to ``session``."""
    return UnitOfWork(
        session=session,
        users=UserRepository(session),
        organizations=OrganizationRepository(session),
        sessions=SessionRepository(session),
        password_resets=PasswordResetRepository(session),
        documents=DocumentRepository(session),
        chunks=DocumentChunkRepository(session),
        chats=ChatRepository(session),
        messages=MessageRepository(session),
        settings=SettingsRepository(session),
        audit_logs=AuditLogRepository(session),
        analytics=AnalyticsRepository(session),
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async for session in get_db_session():
        yield session


async def get_uow(session: AsyncSession = Depends(get_db)) -> UnitOfWork:
    """FastAPI dependency returning a Unit of Work."""
    return build_uow(session)


def get_app_settings() -> Settings:
    """Settings dependency (thin alias for FastAPI Depends)."""
    return get_settings()


def get_default_llm() -> LLMProvider:
    """Resolve the configured default LLM provider."""
    return get_llm_provider()


def get_default_embeddings() -> EmbeddingProvider:
    """Resolve the configured default embedding provider."""
    return get_embedding_provider()


def get_vector_store() -> VectorStore:
    """Resolve Chroma vector store adapter."""
    return VectorStore()
