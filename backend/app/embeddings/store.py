"""ChromaDB vector store adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.db.enums import DocumentScope
from app.db.models.document import Document, DocumentChunk


@dataclass(slots=True)
class VectorSearchHit:
    """Normalized hit returned from a Chroma collection query."""

    id: str
    content: str
    metadata: dict[str, Any]
    distance: float | None = None
    embedding: list[float] | None = None


class VectorStore:
    """Thin adapter around ChromaDB HTTP client.

    Collections are keyed by tenancy:
    - Personal: ``kb_{user_id}``
    - Organization: ``kb_org_{org_id}``
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.HttpClient(
                host=self.settings.chroma_host,
                port=self.settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    @staticmethod
    def personal_collection_name(user_id: str) -> str:
        return f"kb_{user_id}"

    @staticmethod
    def org_collection_name(org_id: str) -> str:
        return f"kb_org_{org_id}"

    def collection_name_for_document(self, document: Document) -> str:
        """Resolve the Chroma collection for a document's tenancy scope."""
        if document.scope == DocumentScope.ORGANIZATION.value and document.organization_id:
            return self.org_collection_name(document.organization_id)
        return self.personal_collection_name(document.owner_id)

    def get_or_create_collection(self, name: str) -> Any:
        """Get or create a named collection."""
        return self.client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})

    def _get_collection(self, name: str) -> Any | None:
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return None

    @staticmethod
    def _chunk_metadata(document: Document, chunk: DocumentChunk) -> dict[str, str | int]:
        return {
            "document_id": document.id,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number if chunk.page_number is not None else -1,
            "title": document.title,
            "scope": document.scope,
            "owner_id": document.owner_id,
        }

    def upsert_chunks(
        self,
        collection_name: str,
        document: Document,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Upsert chunk vectors into the target collection."""
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")

        collection = self.get_or_create_collection(collection_name)
        ids = [chunk.id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [self._chunk_metadata(document, chunk) for chunk in chunks]
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def delete_document_vectors(self, document: Document) -> None:
        """Remove all vectors belonging to a document."""
        collection_name = self.collection_name_for_document(document)
        collection = self._get_collection(collection_name)
        if collection is None:
            return
        try:
            collection.delete(where={"document_id": document.id})
        except Exception:
            return

    def delete_chunk_vectors(self, collection_name: str, chunk_ids: list[str]) -> None:
        """Remove specific chunk vectors by Chroma id."""
        if not chunk_ids:
            return
        collection = self._get_collection(collection_name)
        if collection is None:
            return
        try:
            collection.delete(ids=chunk_ids)
        except Exception:
            return

    def query_semantic(
        self,
        collection_name: str,
        query_embedding: list[float],
        *,
        n_results: int = 20,
        where: dict[str, Any] | None = None,
    ) -> list[VectorSearchHit]:
        """Vector similarity search in a collection."""
        collection = self._get_collection(collection_name)
        if collection is None:
            return []

        try:
            response = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances", "embeddings"],
            )
        except Exception:
            return []

        return self._normalize_query_response(response)

    def query_keyword(
        self,
        collection_name: str,
        query_text: str,
        *,
        n_results: int = 20,
        where: dict[str, Any] | None = None,
    ) -> list[VectorSearchHit]:
        """Keyword search using Chroma document filters."""
        collection = self._get_collection(collection_name)
        if collection is None or not query_text.strip():
            return []

        try:
            response = collection.get(
                where=where,
                where_document={"$contains": query_text},
                limit=n_results,
                include=["documents", "metadatas", "embeddings"],
            )
        except Exception:
            return []

        return self._normalize_get_response(response)

    @staticmethod
    def _normalize_query_response(response: dict[str, Any]) -> list[VectorSearchHit]:
        ids = (response.get("ids") or [[]])[0]
        documents = (response.get("documents") or [[]])[0]
        metadatas = (response.get("metadatas") or [[]])[0]
        distances = (response.get("distances") or [[]])[0]
        embeddings = (response.get("embeddings") or [[]])[0]

        hits: list[VectorSearchHit] = []
        for index, hit_id in enumerate(ids):
            hits.append(
                VectorSearchHit(
                    id=hit_id,
                    content=documents[index] if index < len(documents) else "",
                    metadata=metadatas[index] if index < len(metadatas) else {},
                    distance=distances[index] if index < len(distances) else None,
                    embedding=embeddings[index] if index < len(embeddings) else None,
                )
            )
        return hits

    @staticmethod
    def _normalize_get_response(response: dict[str, Any]) -> list[VectorSearchHit]:
        ids = response.get("ids") or []
        documents = response.get("documents") or []
        metadatas = response.get("metadatas") or []
        embeddings = response.get("embeddings") or []

        hits: list[VectorSearchHit] = []
        for index, hit_id in enumerate(ids):
            hits.append(
                VectorSearchHit(
                    id=hit_id,
                    content=documents[index] if index < len(documents) else "",
                    metadata=metadatas[index] if index < len(metadatas) else {},
                    embedding=embeddings[index] if index < len(embeddings) else None,
                )
            )
        return hits

    def delete_collection(self, collection_name: str) -> None:
        """Delete an entire Chroma collection (e.g. when removing an organization)."""
        try:
            self.client.delete_collection(name=collection_name)
        except Exception:
            return

    def heartbeat(self) -> bool:
        """Return True if Chroma is reachable."""
        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False
