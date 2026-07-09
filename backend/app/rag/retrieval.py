"""Hybrid retrieval orchestration over Chroma collections."""

from __future__ import annotations

from typing import Any, Literal

from app.core.config import Settings, get_settings
from app.core.embedding_cache import get_cached_query_embedding, set_cached_query_embedding
from app.embeddings.factory import get_embedding_provider
from app.embeddings.protocol import EmbeddingProvider
from app.embeddings.store import VectorSearchHit, VectorStore
from app.rag.citations import RetrievedChunk
from app.rag.hybrid import bm25_score, distance_to_similarity, fuse_hybrid_results, keyword_overlap_score
from app.rag.mmr import maximal_marginal_relevance

SearchMode = Literal["semantic", "keyword", "hybrid"]


class RetrievalEngine:
    """Embed queries and retrieve ranked chunks from one or more collections."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        vector_store: VectorStore | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.vector_store = vector_store or VectorStore(self.settings)
        self._embedding_provider = embedding_provider

    async def retrieve(
        self,
        query: str,
        collection_names: list[str],
        *,
        mode: SearchMode = "hybrid",
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        mmr_lambda: float | None = None,
        hybrid_alpha: float | None = None,
        document_ids: list[str] | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        embedding_model: str | None = None,
    ) -> tuple[list[RetrievedChunk], int]:
        """Return ranked chunks and raw candidate count before thresholding."""
        if not collection_names:
            return [], 0

        provider = embedding_provider or self._embedding_provider or get_embedding_provider(
            settings=self.settings
        )
        resolved_top_k = top_k or self.settings.rag_top_k
        candidate_k = max(resolved_top_k * 4, 20)
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.settings.rag_similarity_threshold
        )
        lambda_mult = mmr_lambda if mmr_lambda is not None else self.settings.rag_mmr_lambda
        alpha = hybrid_alpha if hybrid_alpha is not None else self.settings.rag_hybrid_alpha
        where = self._build_where_filter(document_ids)

        semantic_hits: list[RetrievedChunk] = []
        keyword_hits: list[RetrievedChunk] = []

        query_embedding: list[float] | None = None
        if mode in {"semantic", "hybrid"}:
            provider_name = getattr(provider, "name", "default")
            cached = await get_cached_query_embedding(provider_name, embedding_model, query)
            if cached is not None:
                query_embedding = cached
            else:
                query_embedding = await provider.embed_query(query, model=embedding_model)
                await set_cached_query_embedding(
                    provider_name,
                    embedding_model,
                    query,
                    query_embedding,
                )

        for collection_name in collection_names:
            if mode in {"semantic", "hybrid"} and query_embedding is not None:
                for hit in self.vector_store.query_semantic(
                    collection_name,
                    query_embedding,
                    n_results=candidate_k,
                    where=where,
                ):
                    semantic_hits.append(self._hit_to_chunk(hit, collection_name, mode="semantic"))

            if mode in {"keyword", "hybrid"}:
                for hit in self.vector_store.query_keyword(
                    collection_name,
                    query,
                    n_results=candidate_k,
                    where=where,
                ):
                    keyword_hits.append(self._hit_to_chunk(hit, collection_name, mode="keyword", query=query))

        if mode == "semantic":
            candidates = semantic_hits
        elif mode == "keyword":
            candidates = keyword_hits
        else:
            candidates = fuse_hybrid_results(semantic_hits, keyword_hits, alpha=alpha)

        raw_count = len(candidates)
        filtered = [item for item in candidates if item.score >= threshold]
        ranked = maximal_marginal_relevance(filtered, lambda_mult=lambda_mult, top_k=resolved_top_k)
        return ranked, raw_count

    @staticmethod
    def _build_where_filter(document_ids: list[str] | None) -> dict[str, Any] | None:
        if not document_ids:
            return None
        if len(document_ids) == 1:
            return {"document_id": document_ids[0]}
        return {"document_id": {"$in": document_ids}}

    def _hit_to_chunk(
        self,
        hit: VectorSearchHit,
        collection_name: str,
        *,
        mode: str,
        query: str = "",
    ) -> RetrievedChunk:
        metadata = hit.metadata or {}
        page_number = metadata.get("page_number")
        parsed_page = int(page_number) if isinstance(page_number, int) and page_number >= 0 else None
        if isinstance(page_number, str) and page_number.isdigit() and int(page_number) >= 0:
            parsed_page = int(page_number)

        semantic_score = distance_to_similarity(hit.distance) if mode == "semantic" else 0.0
        keyword_score = (
            bm25_score(query, hit.content) if mode == "keyword" else 0.0
        )
        score = semantic_score if mode == "semantic" else keyword_score

        return RetrievedChunk(
            chunk_id=str(metadata.get("chunk_id") or hit.id),
            document_id=str(metadata.get("document_id") or ""),
            title=str(metadata.get("title") or "Untitled"),
            content=hit.content,
            page_number=parsed_page,
            chunk_index=int(metadata.get("chunk_index") or 0),
            score=score,
            semantic_score=semantic_score,
            keyword_score=keyword_score,
            scope=str(metadata.get("scope") or "personal"),
            collection=collection_name,
            embedding=hit.embedding,
        )
