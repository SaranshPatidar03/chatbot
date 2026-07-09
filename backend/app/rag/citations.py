"""Retrieved chunk and citation models for RAG."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RetrievedChunk:
    """A ranked knowledge chunk returned by retrieval."""

    chunk_id: str
    document_id: str
    title: str
    content: str
    page_number: int | None
    chunk_index: int
    score: float
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    scope: str = "personal"
    collection: str = ""
    embedding: list[float] | None = field(default=None, repr=False)

    def citation_label(self) -> str:
        """Human-readable citation label for UI and prompts."""
        page = f", p.{self.page_number}" if self.page_number and self.page_number > 0 else ""
        return f"{self.title} (chunk {self.chunk_index}{page})"

    def to_context_block(self) -> str:
        """Format chunk for grounded LLM context."""
        return (
            f"[Source: {self.citation_label()} | score={self.score:.3f}]\n"
            f"{self.content}"
        )


def chunk_to_citation_dict(chunk: RetrievedChunk) -> dict:
    """Serialize a retrieved chunk for API / message storage."""
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "title": chunk.title,
        "content_preview": chunk.content[:400],
        "page_number": chunk.page_number,
        "chunk_index": chunk.chunk_index,
        "score": round(chunk.score, 4),
        "citation": chunk.citation_label(),
    }
