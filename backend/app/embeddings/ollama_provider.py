"""Ollama embeddings provider."""

import httpx

from app.core.config import Settings, get_settings
from app.embeddings.protocol import EmbeddingResult


class OllamaEmbeddingProvider:
    """EmbeddingProvider backed by Ollama `/api/embeddings`."""

    name = "ollama"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.default_model = self.settings.ollama_embedding_model

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        selected_model = model or self.default_model
        vectors: list[list[float]] = []

        async with httpx.AsyncClient(timeout=120.0) as client:
            for text in texts:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": selected_model, "prompt": text},
                )
                response.raise_for_status()
                data = response.json()
                vectors.append(data["embedding"])

        dimensions = len(vectors[0]) if vectors else 0
        return EmbeddingResult(
            vectors=vectors,
            model=selected_model,
            provider=self.name,
            dimensions=dimensions,
        )

    async def embed_query(self, text: str, *, model: str | None = None) -> list[float]:
        result = await self.embed([text], model=model)
        return result.vectors[0]
