"""Pydantic schemas for knowledge search APIs."""

from typing import Literal

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    document_ids: list[str] | None = None
    scope: Literal["personal", "organization", "all"] = "all"
    organization_id: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    mode: Literal["semantic", "keyword", "hybrid"] = "hybrid"
    top_k: int | None = Field(default=None, ge=1, le=50)
    filters: SearchFilters | None = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    content: str
    page_number: int | None
    chunk_index: int
    score: float
    semantic_score: float
    keyword_score: float
    scope: str
    citation: str


class SearchResponse(BaseModel):
    query: str
    mode: str
    results: list[SearchResultItem]
    total_candidates: int
    has_sufficient_context: bool
