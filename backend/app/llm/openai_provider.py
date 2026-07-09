"""OpenAI chat completions provider."""

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from app.core.config import Settings, get_settings
from app.llm.protocol import ChatMessage, LLMResponse, StreamChunk


class OpenAILLMProvider:
    """LLMProvider implementation backed by the OpenAI API."""

    name = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = AsyncOpenAI(
            api_key=self.settings.openai_api_key or "missing-key",
            base_url=self.settings.openai_base_url,
        )
        self.default_model = self.settings.openai_default_model

    async def list_models(self) -> list[str]:
        response = await self._client.models.list()
        return sorted(model.id for model in response.data)

    def _to_openai_messages(self, messages: list[ChatMessage]) -> list[dict[str, str]]:
        return [{"role": message.role, "content": message.content} for message in messages]

    async def generate(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        top_p: float = 1.0,
        max_tokens: int = 1024,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        selected_model = model or self.default_model
        kwargs: dict[str, Any] = {
            "model": selected_model,
            "messages": self._to_openai_messages(messages),
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        if stop:
            kwargs["stop"] = stop

        completion = await self._client.chat.completions.create(**kwargs)
        choice = completion.choices[0]
        usage = completion.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=completion.model,
            provider=self.name,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            total_tokens=usage.total_tokens if usage else None,
            raw=completion.model_dump(),
        )

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        top_p: float = 1.0,
        max_tokens: int = 1024,
        stop: list[str] | None = None,
    ) -> AsyncIterator[StreamChunk]:
        selected_model = model or self.default_model
        kwargs: dict[str, Any] = {
            "model": selected_model,
            "messages": self._to_openai_messages(messages),
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if stop:
            kwargs["stop"] = stop

        stream = await self._client.chat.completions.create(**kwargs)
        async for event in stream:
            delta = event.choices[0].delta.content if event.choices else None
            if delta:
                yield StreamChunk(
                    content=delta,
                    done=False,
                    model=selected_model,
                    provider=self.name,
                )
        yield StreamChunk(content="", done=True, model=selected_model, provider=self.name)
