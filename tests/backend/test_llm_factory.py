from app.llm.factory import get_llm_provider, clear_llm_provider_cache


def test_get_llm_provider_ollama() -> None:
    clear_llm_provider_cache()
    provider = get_llm_provider("ollama", use_cache=False)
    assert provider.name == "ollama"


def test_get_llm_provider_openai() -> None:
    clear_llm_provider_cache()
    provider = get_llm_provider("openai", use_cache=False)
    assert provider.name == "openai"
