"""Factory for resolving LLM providers by name."""

from typing import Literal

from app.core.config import Settings, get_settings
from app.llm.ollama_provider import OllamaLLMProvider
from app.llm.openai_provider import OpenAILLMProvider
from app.llm.protocol import LLMProvider

ProviderName = Literal["openai", "ollama"]

_PROVIDER_CACHE: dict[str, LLMProvider] = {}


def get_llm_provider(
    name: ProviderName | None = None,
    *,
    settings: Settings | None = None,
    use_cache: bool = True,
) -> LLMProvider:
    """Return an LLM provider instance.

    New providers register here — one class + one factory branch.
    """
    cfg = settings or get_settings()
    provider_name: ProviderName = name or cfg.default_llm_provider

    if use_cache and provider_name in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[provider_name]

    if provider_name == "openai":
        provider: LLMProvider = OpenAILLMProvider(cfg)
    elif provider_name == "ollama":
        provider = OllamaLLMProvider(cfg)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")

    if use_cache:
        _PROVIDER_CACHE[provider_name] = provider
    return provider


def clear_llm_provider_cache() -> None:
    """Clear cached providers (useful in tests)."""
    _PROVIDER_CACHE.clear()
