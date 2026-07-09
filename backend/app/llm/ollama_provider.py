"""Ollama chat completions provider (OpenAI-compatible HTTP API)."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.llm.protocol import ChatMessage, LLMResponse, StreamChunk


class OllamaLLMProvider:
    """LLMProvider implementation for local Ollama models."""

    name = "ollama"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.default_model = self.settings.ollama_default_model

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
            return sorted(model["name"] for model in payload.get("models", []))

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
        body: dict[str, Any] = {
            "model": selected_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens,
            },
        }
        if stop:
            body["options"]["stop"] = stop

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=body)
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        return LLMResponse(
            content=content,
            model=selected_model,
            provider=self.name,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            total_tokens=(
                (data.get("prompt_eval_count") or 0) + (data.get("eval_count") or 0)
                if data.get("prompt_eval_count") is not None or data.get("eval_count") is not None
                else None
            ),
            raw=data,
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
        body: dict[str, Any] = {
            "model": selected_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens,
            },
        }
        if stop:
            body["options"]["stop"] = stop

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=body) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    done = bool(data.get("done"))
                    if content:
                        yield StreamChunk(
                            content=content,
                            done=False,
                            model=selected_model,
                            provider=self.name,
                        )
                    if done:
                        yield StreamChunk(
                            content="",
                            done=True,
                            model=selected_model,
                            provider=self.name,
                        )
                        return

        yield StreamChunk(content="", done=True, model=selected_model, provider=self.name)
