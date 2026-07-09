"""MMR unit tests."""

from app.rag.citations import RetrievedChunk
from app.rag.mmr import maximal_marginal_relevance


def _chunk(chunk_id: str, score: float, embedding: list[float]) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        title="Doc",
        content=f"content {chunk_id}",
        page_number=None,
        chunk_index=0,
        score=score,
        embedding=embedding,
    )


def test_mmr_prefers_relevance_when_lambda_is_one() -> None:
    candidates = [
        _chunk("a", 0.9, [1.0, 0.0]),
        _chunk("b", 0.8, [0.9, 0.1]),
        _chunk("c", 0.7, [0.0, 1.0]),
    ]
    selected = maximal_marginal_relevance(candidates, lambda_mult=1.0, top_k=2)
    assert [item.chunk_id for item in selected] == ["a", "b"]


def test_mmr_promotes_diversity_when_lambda_is_low() -> None:
    candidates = [
        _chunk("a", 0.9, [1.0, 0.0, 0.0]),
        _chunk("b", 0.88, [0.99, 0.01, 0.0]),
        _chunk("c", 0.7, [0.0, 1.0, 0.0]),
    ]
    selected = maximal_marginal_relevance(candidates, lambda_mult=0.2, top_k=2)
    assert selected[0].chunk_id == "a"
    assert selected[1].chunk_id == "c"
