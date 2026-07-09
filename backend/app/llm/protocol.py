"""Protocol defining a pluggable LLM provider."""

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat turn for provider APIs."""

    role: str
    content: str


class LLMResponse(BaseModel):
    """Non-streaming completion result."""

    content: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
    """Incremental streamed token payload."""

    content: str
    done: bool = False
    model: str | None = None
    provider: str | None = None


@runtime_checkable
class LLMProvider(Protocol):
    """Interface every LLM backend must implement."""

    name: str

    async def list_models(self) -> list[str]:
        """Return available model identifiers."""
        ...

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
        """Generate a full completion."""
        ...

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
        """Yield streamed completion chunks."""
        ...
