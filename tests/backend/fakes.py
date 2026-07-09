"""Test doubles for embedding and vector-store dependencies."""

from __future__ import annotations

import math

from app.db.models.document import Document, DocumentChunk
from app.embeddings.protocol import EmbeddingResult
from app.embeddings.store import VectorSearchHit
from app.llm.protocol import LLMResponse, StreamChunk
from app.rag.hybrid import keyword_overlap_score


class FakeLLMProvider:
    """Deterministic LLM provider for chat integration tests."""

    name = "fake"
    default_text = "According to the retrieved documents, the leave policy grants 20 days per year."

    async def list_models(self) -> list[str]:
        return ["fake-model"]

    async def generate(
        self,
        messages,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        top_p: float = 1.0,
        max_tokens: int = 1024,
        stop=None,
    ) -> LLMResponse:
        return LLMResponse(
            content=self.default_text,
            model=model or "fake-model",
            provider=self.name,
        )

    async def stream(
        self,
        messages,
        *,
        model: str | None = None,
        temperature: float = 0.2,
        top_p: float = 1.0,
        max_tokens: int = 1024,
        stop=None,
    ):
        for part in self.default_text.split():
            yield StreamChunk(content=part + " ", model=model or "fake-model", provider=self.name)
        yield StreamChunk(content="", done=True, model=model or "fake-model", provider=self.name)


class FakeEmbeddingProvider:
    """Deterministic embedding provider for tests."""

    name = "fake"

    def __init__(self, dimensions: int = 8) -> None:
        self.dimensions = dimensions

    async def embed(self, texts: list[str], *, model: str | None = None) -> EmbeddingResult:
        vectors = [
            [float((index + char_index) % 7) / 7 for char_index in range(self.dimensions)]
            for index, _ in enumerate(texts)
        ]
        return EmbeddingResult(
            vectors=vectors,
            model=model or "fake-embedding-model",
            provider=self.name,
            dimensions=self.dimensions,
        )

    async def embed_query(self, text: str, *, model: str | None = None) -> list[float]:
        result = await self.embed([text], model=model)
        return result.vectors[0]


class InMemoryVectorStore:
    """In-memory Chroma substitute for unit and integration tests."""

    def __init__(self, settings=None) -> None:
        self.settings = settings
        self.collections: dict[str, dict[str, dict]] = {}

    @staticmethod
    def personal_collection_name(user_id: str) -> str:
        return f"kb_{user_id}"

    @staticmethod
    def org_collection_name(org_id: str) -> str:
        return f"kb_org_{org_id}"

    def collection_name_for_document(self, document: Document) -> str:
        if document.organization_id:
            return self.org_collection_name(document.organization_id)
        return self.personal_collection_name(document.owner_id)

    def upsert_chunks(
        self,
        collection_name: str,
        document: Document,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        bucket = self.collections.setdefault(collection_name, {})
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            bucket[chunk.id] = {
                "embedding": embedding,
                "document_id": document.id,
                "content": chunk.content,
                "title": document.title,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number if chunk.page_number is not None else -1,
                "scope": document.scope,
                "owner_id": document.owner_id,
            }

    def delete_document_vectors(self, document: Document) -> None:
        collection_name = self.collection_name_for_document(document)
        bucket = self.collections.get(collection_name)
        if not bucket:
            return
        for chunk_id in list(bucket):
            if bucket[chunk_id]["document_id"] == document.id:
                del bucket[chunk_id]

    def query_semantic(
        self,
        collection_name: str,
        query_embedding: list[float],
        *,
        n_results: int = 20,
        where: dict | None = None,
    ) -> list[VectorSearchHit]:
        bucket = self.collections.get(collection_name, {})
        scored: list[tuple[float, VectorSearchHit]] = []
        for chunk_id, item in bucket.items():
            if not self._matches_where(item, where):
                continue
            distance = 1.0 - _cosine_similarity(query_embedding, item["embedding"])
            scored.append(
                (
                    distance,
                    VectorSearchHit(
                        id=chunk_id,
                        content=item["content"],
                        metadata=self._metadata_from_item(item),
                        distance=distance,
                        embedding=item["embedding"],
                    ),
                )
            )
        scored.sort(key=lambda pair: pair[0])
        return [hit for _, hit in scored[:n_results]]

    def query_keyword(
        self,
        collection_name: str,
        query_text: str,
        *,
        n_results: int = 20,
        where: dict | None = None,
    ) -> list[VectorSearchHit]:
        bucket = self.collections.get(collection_name, {})
        scored: list[tuple[float, VectorSearchHit]] = []
        for chunk_id, item in bucket.items():
            if not self._matches_where(item, where):
                continue
            score = keyword_overlap_score(query_text, item["content"])
            if score <= 0:
                continue
            scored.append(
                (
                    -score,
                    VectorSearchHit(
                        id=chunk_id,
                        content=item["content"],
                        metadata=self._metadata_from_item(item),
                        distance=1.0 - score,
                        embedding=item["embedding"],
                    ),
                )
            )
        scored.sort(key=lambda pair: pair[0])
        return [hit for _, hit in scored[:n_results]]

    @staticmethod
    def _metadata_from_item(item: dict) -> dict:
        return {
            "document_id": item["document_id"],
            "chunk_id": item["chunk_id"],
            "chunk_index": item["chunk_index"],
            "page_number": item["page_number"],
            "title": item["title"],
            "scope": item["scope"],
            "owner_id": item["owner_id"],
        }

    @staticmethod
    def _matches_where(item: dict, where: dict | None) -> bool:
        if not where:
            return True
        if "document_id" in where:
            expected = where["document_id"]
            if isinstance(expected, dict) and "$in" in expected:
                return item["document_id"] in expected["$in"]
            return item["document_id"] == expected
        return True

    def heartbeat(self) -> bool:
        return True

    def count_for_document(self, document: Document) -> int:
        collection_name = self.collection_name_for_document(document)
        bucket = self.collections.get(collection_name, {})
        return sum(1 for item in bucket.values() if item["document_id"] == document.id)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
