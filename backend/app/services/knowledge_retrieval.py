"""Shared knowledge retrieval for search and chat."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.deps import UnitOfWork
from app.db.enums import DocumentStatus
from app.db.models.user import User
from app.embeddings.factory import ProviderName, get_embedding_provider
from app.embeddings.store import VectorStore
from app.rag.citations import RetrievedChunk
from app.rag.retrieval import RetrievalEngine, SearchMode
from app.schemas.search import SearchFilters


class KnowledgeRetrieval:
    """Retrieve grounded chunks for a user across personal and org collections."""

    def __init__(self, uow: UnitOfWork, settings: Settings | None = None) -> None:
        self.uow = uow
        self.settings = settings or get_settings()

    async def retrieve(
        self,
        user: User,
        query: str,
        *,
        mode: SearchMode = "hybrid",
        top_k: int | None = None,
        filters: SearchFilters | None = None,
    ) -> tuple[list[RetrievedChunk], int, float, bool]:
        """Return chunks, raw candidate count, threshold, and sufficient-context flag."""
        filters = filters or SearchFilters()
        collections = await self.resolve_collections(user, filters)
        if not collections:
            return [], 0, self.settings.rag_similarity_threshold, False

        user_settings = await self.uow.settings.get_for_user(user.id)
        resolved_top_k = top_k or (user_settings.top_k if user_settings else self.settings.rag_top_k)
        similarity_threshold = (
            user_settings.similarity_threshold
            if user_settings
            else self.settings.rag_similarity_threshold
        )
        mmr_lambda = user_settings.mmr_lambda if user_settings else self.settings.rag_mmr_lambda

        provider_name: ProviderName = (
            user_settings.embedding_provider  # type: ignore[assignment]
            if user_settings
            else self.settings.default_embedding_provider
        )
        embedding_model = (
            user_settings.embedding_model
            if user_settings
            else (
                self.settings.openai_embedding_model
                if provider_name == "openai"
                else self.settings.ollama_embedding_model
            )
        )
        provider = get_embedding_provider(provider_name, settings=self.settings)

        engine = RetrievalEngine(self.settings)
        results, raw_count = await engine.retrieve(
            query,
            collections,
            mode=mode,
            top_k=resolved_top_k,
            similarity_threshold=similarity_threshold,
            mmr_lambda=mmr_lambda,
            document_ids=filters.document_ids,
            embedding_provider=provider,
            embedding_model=embedding_model,
        )
        results = await self._filter_accessible(user, results)
        has_context = any(item.score >= similarity_threshold for item in results)
        return results, raw_count, similarity_threshold, has_context

    async def resolve_collections(self, user: User, filters: SearchFilters) -> list[str]:
        collections: list[str] = []

        if filters.scope in {"all", "personal"}:
            collections.append(VectorStore.personal_collection_name(user.id))

        if filters.scope in {"all", "organization"}:
            if filters.organization_id:
                membership = await self.uow.organizations.get_membership(
                    filters.organization_id,
                    user.id,
                )
                if membership is None:
                    return []
                collections.append(VectorStore.org_collection_name(filters.organization_id))
            else:
                orgs = await self.uow.organizations.list_for_user(user.id)
                collections.extend(VectorStore.org_collection_name(org.id) for org in orgs)

        return list(dict.fromkeys(collections))

    async def _filter_accessible(self, user: User, hits: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not hits:
            return []

        document_ids = list({hit.document_id for hit in hits if hit.document_id})
        documents = await self.uow.documents.get_by_ids(document_ids)
        org_ids = list(
            {doc.organization_id for doc in documents if doc.organization_id}
        )
        member_org_ids = await self.uow.organizations.membership_org_ids_for_user(
            user.id,
            org_ids,
        )
        allowed_ids: set[str] = set()

        for document in documents:
            if document.status != DocumentStatus.READY.value:
                continue
            if document.owner_id == user.id:
                allowed_ids.add(document.id)
                continue
            if document.organization_id and document.organization_id in member_org_ids:
                allowed_ids.add(document.id)

        return [hit for hit in hits if hit.document_id in allowed_ids]
