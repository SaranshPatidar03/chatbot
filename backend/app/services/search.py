"""Knowledge-base search use cases."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.core.deps import UnitOfWork
from app.core.logging import get_logger
from app.db.enums import AnalyticsEventType
from app.db.models.user import User
from app.schemas.search import SearchFilters, SearchRequest, SearchResponse, SearchResultItem
from app.services.knowledge_retrieval import KnowledgeRetrieval

logger = get_logger(__name__)


class SearchService:
    """Search the authenticated user's knowledge collections."""

    def __init__(self, uow: UnitOfWork, settings: Settings | None = None) -> None:
        self.uow = uow
        self.settings = settings or get_settings()

    async def search(self, user: User, payload: SearchRequest) -> SearchResponse:
        filters = payload.filters or SearchFilters()
        retriever = KnowledgeRetrieval(self.uow, self.settings)
        collections = await retriever.resolve_collections(user, filters)
        if not collections:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No searchable collections available for this scope.",
            )

        user_settings = await self.uow.settings.get_for_user(user.id)
        top_k = payload.top_k or (user_settings.top_k if user_settings else self.settings.rag_top_k)

        results, raw_count, threshold, has_context = await retriever.retrieve(
            user,
            payload.query,
            mode=payload.mode,
            top_k=top_k,
            filters=filters,
        )

        await self.uow.analytics.record(
            user_id=user.id,
            event_type=AnalyticsEventType.RETRIEVAL.value,
            name="knowledge_search",
            status="success",
            meta={
                "mode": payload.mode,
                "query_length": len(payload.query),
                "results": len(results),
                "candidates": raw_count,
            },
        )
        logger.info(
            "knowledge_search",
            user_id=user.id,
            mode=payload.mode,
            results=len(results),
            candidates=raw_count,
        )

        return SearchResponse(
            query=payload.query,
            mode=payload.mode,
            results=[self._to_result_item(item) for item in results],
            total_candidates=raw_count,
            has_sufficient_context=has_context,
        )

    @staticmethod
    def _to_result_item(hit) -> SearchResultItem:
        return SearchResultItem(
            chunk_id=hit.chunk_id,
            document_id=hit.document_id,
            title=hit.title,
            content=hit.content,
            page_number=hit.page_number,
            chunk_index=hit.chunk_index,
            score=round(hit.score, 4),
            semantic_score=round(hit.semantic_score, 4),
            keyword_score=round(hit.keyword_score, 4),
            scope=hit.scope,
            citation=hit.citation_label(),
        )
