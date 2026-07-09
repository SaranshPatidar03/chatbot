"""Embed document chunks and index them in ChromaDB."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.deps import UnitOfWork
from app.core.logging import get_logger
from app.db.enums import AnalyticsEventType
from app.db.models.document import Document, DocumentChunk
from app.embeddings.factory import ProviderName, get_embedding_provider
from app.embeddings.protocol import EmbeddingProvider
from app.embeddings.store import VectorStore

logger = get_logger(__name__)


class IndexService:
    """Generate embeddings and persist vectors for document chunks."""

    def __init__(
        self,
        uow: UnitOfWork,
        settings: Settings | None = None,
        *,
        vector_store: VectorStore | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.uow = uow
        self.settings = settings or get_settings()
        self.vector_store = vector_store or VectorStore(self.settings)
        self._embedding_provider = embedding_provider

    async def index_chunks(self, document: Document, chunks: list[DocumentChunk]) -> int:
        """Embed and upsert chunks. Returns the number of vectors indexed."""
        if not chunks:
            return 0

        provider, model = await self._resolve_embedding(document.owner_id)
        collection_name = self.vector_store.collection_name_for_document(document)
        batch_size = max(self.settings.embedding_batch_size, 1)
        indexed = 0

        for offset in range(0, len(chunks), batch_size):
            batch = chunks[offset : offset + batch_size]
            texts = [chunk.content for chunk in batch]
            result = await provider.embed(texts, model=model)
            self.vector_store.upsert_chunks(collection_name, document, batch, result.vectors)

            for chunk in batch:
                chunk.chroma_id = chunk.id
                chunk.embedding_model = result.model
            indexed += len(batch)

        await self.uow.session.flush()
        await self.uow.analytics.record(
            user_id=document.owner_id,
            event_type=AnalyticsEventType.EMBEDDING.value,
            name="document_indexed",
            status="success",
            meta={
                "document_id": document.id,
                "chunks": indexed,
                "model": model,
                "provider": provider.name,
            },
        )
        logger.info(
            "document_indexed",
            document_id=document.id,
            chunks=indexed,
            model=model,
            provider=provider.name,
        )
        return indexed

    async def purge_document_vectors(self, document: Document) -> None:
        """Remove all vectors for a document from Chroma."""
        self.vector_store.delete_document_vectors(document)

    async def _resolve_embedding(self, user_id: str) -> tuple[EmbeddingProvider, str | None]:
        if self._embedding_provider is not None:
            return self._embedding_provider, None

        user_settings = await self.uow.settings.get_for_user(user_id)
        provider_name: ProviderName = (
            user_settings.embedding_provider  # type: ignore[assignment]
            if user_settings
            else self.settings.default_embedding_provider
        )
        model = (
            user_settings.embedding_model
            if user_settings
            else self._default_model_for_provider(provider_name)
        )
        provider = get_embedding_provider(provider_name, settings=self.settings)
        return provider, model

    def _default_model_for_provider(self, provider_name: str) -> str:
        if provider_name == "openai":
            return self.settings.openai_embedding_model
        return self.settings.ollama_embedding_model
