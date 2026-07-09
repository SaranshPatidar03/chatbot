"""Hybrid semantic + keyword score fusion."""

from __future__ import annotations

import math
import re
from collections import Counter

from app.rag.citations import RetrievedChunk


def keyword_overlap_score(query: str, text: str) -> float:
    """Simple token-overlap score in ``[0, 1]`` for keyword retrieval."""
    query_terms = {term for term in _tokenize(query) if len(term) > 1}
    if not query_terms:
        return 0.0
    text_terms = set(_tokenize(text))
    if not text_terms:
        return 0.0
    overlap = len(query_terms & text_terms)
    return overlap / len(query_terms)


def bm25_score(
    query: str,
    text: str,
    *,
    avg_doc_len: float = 500.0,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Lightweight BM25-style relevance score normalized to ``[0, 1]``."""
    query_terms = [term for term in _tokenize(query) if len(term) > 1]
    doc_terms = _tokenize(text)
    if not query_terms or not doc_terms:
        return 0.0

    doc_len = len(doc_terms)
    term_freq = Counter(doc_terms)
    unique_query = set(query_terms)
    raw = 0.0

    for term in unique_query:
        tf = term_freq.get(term, 0)
        if tf == 0:
            continue
        idf = math.log(1.0 + (1.0 + avg_doc_len) / (1.0 + tf))
        denom = tf + k1 * (1.0 - b + b * (doc_len / avg_doc_len))
        raw += idf * ((tf * (k1 + 1)) / denom)

    if raw <= 0:
        return 0.0
    return min(raw / len(unique_query), 1.0)


def distance_to_similarity(distance: float | None) -> float:
    """Convert Chroma cosine distance to a similarity score."""
    if distance is None:
        return 0.0
    return max(0.0, 1.0 - distance)


def fuse_hybrid_results(
    semantic_hits: list[RetrievedChunk],
    keyword_hits: list[RetrievedChunk],
    *,
    alpha: float,
) -> list[RetrievedChunk]:
    """Merge semantic and keyword hits with weighted score fusion."""
    alpha = min(max(alpha, 0.0), 1.0)
    merged: dict[str, RetrievedChunk] = {}

    for hit in semantic_hits:
        merged[hit.chunk_id] = RetrievedChunk(
            chunk_id=hit.chunk_id,
            document_id=hit.document_id,
            title=hit.title,
            content=hit.content,
            page_number=hit.page_number,
            chunk_index=hit.chunk_index,
            score=alpha * hit.semantic_score,
            semantic_score=hit.semantic_score,
            keyword_score=0.0,
            scope=hit.scope,
            collection=hit.collection,
            embedding=hit.embedding,
        )

    for hit in keyword_hits:
        existing = merged.get(hit.chunk_id)
        keyword_component = (1.0 - alpha) * hit.keyword_score
        if existing:
            existing.keyword_score = hit.keyword_score
            existing.score = alpha * existing.semantic_score + keyword_component
            if existing.embedding is None:
                existing.embedding = hit.embedding
        else:
            merged[hit.chunk_id] = RetrievedChunk(
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                title=hit.title,
                content=hit.content,
                page_number=hit.page_number,
                chunk_index=hit.chunk_index,
                score=keyword_component,
                semantic_score=0.0,
                keyword_score=hit.keyword_score,
                scope=hit.scope,
                collection=hit.collection,
                embedding=hit.embedding,
            )

    return sorted(merged.values(), key=lambda item: item.score, reverse=True)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())
