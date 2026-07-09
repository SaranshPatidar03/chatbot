"""Shared pytest fixtures for backend integration tests."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

from app.api.deps import get_db
from app.db import models  # noqa: F401 — register metadata
from app.db.base import Base
from app.embeddings.factory import clear_embedding_provider_cache
from app.llm.factory import clear_llm_provider_cache
from app.main import app
from fakes import FakeEmbeddingProvider, FakeLLMProvider, InMemoryVectorStore


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_type, compiler, **kwargs):
    return compiler.visit_JSON(JSON(), **kwargs)


@compiles(UUID, "sqlite")
def _compile_uuid_sqlite(_type, compiler, **kwargs):
    return "CHAR(36)"


@pytest.fixture(autouse=True)
def mock_vector_indexing(monkeypatch):
    """Avoid external Chroma/Ollama during API integration tests."""
    store = InMemoryVectorStore()
    provider = FakeEmbeddingProvider()
    llm = FakeLLMProvider()

    monkeypatch.setattr("app.services.indexing.VectorStore", lambda settings=None: store)
    monkeypatch.setattr("app.embeddings.store.VectorStore", lambda settings=None: store)
    monkeypatch.setattr("app.rag.retrieval.VectorStore", lambda settings=None: store)
    for target in (
        "app.embeddings.factory.get_embedding_provider",
        "app.services.indexing.get_embedding_provider",
        "app.rag.retrieval.get_embedding_provider",
        "app.services.knowledge_retrieval.get_embedding_provider",
    ):
        monkeypatch.setattr(target, lambda *args, **kwargs: provider)
    for target in (
        "app.llm.factory.get_llm_provider",
        "app.services.chat.get_llm_provider",
    ):
        monkeypatch.setattr(target, lambda *args, **kwargs: llm)
    clear_embedding_provider_cache()
    clear_llm_provider_cache()
    yield store
    clear_embedding_provider_cache()
    clear_llm_provider_cache()


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
