"""Factory for resolving embedding providers by name."""

from typing import Literal

from app.core.config import Settings, get_settings
from app.embeddings.ollama_provider import OllamaEmbeddingProvider
from app.embeddings.openai_provider import OpenAIEmbeddingProvider
from app.embeddings.protocol import EmbeddingProvider

ProviderName = Literal["openai", "ollama"]

_PROVIDER_CACHE: dict[str, EmbeddingProvider] = {}


def get_embedding_provider(
    name: ProviderName | None = None,
    *,
    settings: Settings | None = None,
    use_cache: bool = True,
) -> EmbeddingProvider:
    """Return an embedding provider instance."""
    cfg = settings or get_settings()
    provider_name: ProviderName = name or cfg.default_embedding_provider

    if use_cache and provider_name in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[provider_name]

    if provider_name == "openai":
        provider: EmbeddingProvider = OpenAIEmbeddingProvider(cfg)
    elif provider_name == "ollama":
        provider = OllamaEmbeddingProvider(cfg)
    else:
        raise ValueError(f"Unsupported embedding provider: {provider_name}")

    if use_cache:
        _PROVIDER_CACHE[provider_name] = provider
    return provider


def clear_embedding_provider_cache() -> None:
    """Clear cached providers (useful in tests)."""
    _PROVIDER_CACHE.clear()
