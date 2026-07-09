"""Protocol defining a pluggable embedding provider."""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class EmbeddingResult(BaseModel):
    """Batch embedding output."""

    vectors: list[list[float]]
    model: str
    provider: str
    dimensions: int
    total_tokens: int | None = None


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Interface every embedding backend must implement."""

    name: str

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        """Embed one or more texts into dense vectors."""
        ...

    async def embed_query(self, text: str, *, model: str | None = None) -> list[float]:
        """Embed a single query string."""
        ...
