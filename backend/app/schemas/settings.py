"""Pydantic schemas for per-user LLM / RAG settings."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UserSettingsResponse(BaseModel):
    theme: str
    language: str
    llm_provider: Literal["openai", "ollama"]
    llm_model: str
    embedding_provider: Literal["openai", "ollama"]
    embedding_model: str
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int
    system_prompt: str | None
    allow_general_knowledge: bool
    similarity_threshold: float
    mmr_lambda: float
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserSettingsUpdateRequest(BaseModel):
    theme: str | None = Field(default=None, pattern="^(light|dark|system)$")
    language: str | None = Field(default=None, min_length=2, max_length=16)
    llm_provider: Literal["openai", "ollama"] | None = None
    llm_model: str | None = Field(default=None, min_length=1, max_length=128)
    embedding_provider: Literal["openai", "ollama"] | None = None
    embedding_model: str | None = Field(default=None, min_length=1, max_length=128)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    top_k: int | None = Field(default=None, ge=1, le=50)
    max_tokens: int | None = Field(default=None, ge=64, le=8192)
    system_prompt: str | None = Field(default=None, max_length=8000)
    allow_general_knowledge: bool | None = None
    similarity_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    mmr_lambda: float | None = Field(default=None, ge=0.0, le=1.0)
