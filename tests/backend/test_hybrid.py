"""Hybrid fusion unit tests."""

from app.rag.citations import RetrievedChunk
from app.rag.hybrid import fuse_hybrid_results, keyword_overlap_score


def test_keyword_overlap_score() -> None:
    assert keyword_overlap_score("leave policy", "Our leave policy grants 20 days") > 0.5
    assert keyword_overlap_score("zzzz", "no match here") == 0.0


def test_fuse_hybrid_results_combines_scores() -> None:
    semantic = [
        RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            title="Policy",
            content="leave policy details",
            page_number=None,
            chunk_index=0,
            score=0.8,
            semantic_score=0.8,
            embedding=[1.0, 0.0],
        )
    ]
    keyword = [
        RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            title="Policy",
            content="leave policy details",
            page_number=None,
            chunk_index=0,
            score=0.6,
            keyword_score=0.6,
            embedding=[1.0, 0.0],
        ),
        RetrievedChunk(
            chunk_id="chunk-2",
            document_id="doc-1",
            title="Policy",
            content="keyword only hit",
            page_number=None,
            chunk_index=1,
            score=0.5,
            keyword_score=0.5,
            embedding=[0.0, 1.0],
        ),
    ]

    fused = fuse_hybrid_results(semantic, keyword, alpha=0.7)
    by_id = {item.chunk_id: item for item in fused}
    assert by_id["chunk-1"].score == 0.7 * 0.8 + 0.3 * 0.6
    assert "chunk-2" in by_id
