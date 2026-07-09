"""Tests for BM25 keyword scoring."""

from app.rag.hybrid import bm25_score, keyword_overlap_score


def test_bm25_prefers_matching_terms() -> None:
    query = "leave policy annual"
    relevant = "The leave policy grants 20 annual leave days per employee."
    irrelevant = "Database connection pooling improves throughput."
    assert bm25_score(query, relevant) > bm25_score(query, irrelevant)


def test_bm25_returns_zero_for_empty() -> None:
    assert bm25_score("", "some text") == 0.0
    assert bm25_score("query", "") == 0.0


def test_keyword_overlap_still_available() -> None:
    assert keyword_overlap_score("policy leave", "company policy handbook") > 0.0
