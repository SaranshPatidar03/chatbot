"""Maximal Marginal Relevance (MMR) re-ranking."""

from __future__ import annotations

import math

from app.rag.citations import RetrievedChunk


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def maximal_marginal_relevance(
    candidates: list[RetrievedChunk],
    *,
    lambda_mult: float,
    top_k: int,
) -> list[RetrievedChunk]:
    """Select diverse top-k chunks using MMR.

    ``lambda_mult`` near 1.0 favors relevance; near 0.0 favors diversity.
    """
    if not candidates or top_k <= 0:
        return []

    lambda_mult = min(max(lambda_mult, 0.0), 1.0)
    pool = sorted(candidates, key=lambda item: item.score, reverse=True)
    selected: list[RetrievedChunk] = []

    while pool and len(selected) < top_k:
        best_index = 0
        best_mmr = float("-inf")

        for index, candidate in enumerate(pool):
            relevance = candidate.score
            diversity_penalty = 0.0
            if selected and candidate.embedding is not None:
                diversity_penalty = max(
                    _cosine_similarity(candidate.embedding, chosen.embedding or [])
                    for chosen in selected
                    if chosen.embedding is not None
                )
            mmr_score = lambda_mult * relevance - (1.0 - lambda_mult) * diversity_penalty
            if mmr_score > best_mmr:
                best_mmr = mmr_score
                best_index = index

        selected.append(pool.pop(best_index))

    return selected
