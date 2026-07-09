"""OpenAI embeddings provider."""

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.embeddings.protocol import EmbeddingResult


class OpenAIEmbeddingProvider:
    """EmbeddingProvider backed by OpenAI embeddings API."""

    name = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = AsyncOpenAI(
            api_key=self.settings.openai_api_key or "missing-key",
            base_url=self.settings.openai_base_url,
        )
        self.default_model = self.settings.openai_embedding_model

    async def embed(
        self,
        texts: list[str],
        *,
        model: str | None = None,
    ) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(
                vectors=[],
                model=model or self.default_model,
                provider=self.name,
                dimensions=0,
            )

        selected_model = model or self.default_model
        response = await self._client.embeddings.create(model=selected_model, input=texts)
        vectors = [item.embedding for item in response.data]
        dimensions = len(vectors[0]) if vectors else 0
        usage = response.usage
        return EmbeddingResult(
            vectors=vectors,
            model=selected_model,
            provider=self.name,
            dimensions=dimensions,
            total_tokens=usage.total_tokens if usage else None,
        )

    async def embed_query(self, text: str, *, model: str | None = None) -> list[float]:
        result = await self.embed([text], model=model)
        return result.vectors[0]
