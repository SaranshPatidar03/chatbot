"""Health and readiness schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class DependencyStatus(BaseModel):
    """Status of a single runtime dependency."""

    name: str
    status: Literal["ok", "degraded", "unavailable"]
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    """Liveness payload."""

    status: str = Field(description="Overall health status")
    app: str
    version: str
    phase: int = Field(description="Current delivered development phase")
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness payload including dependency probes."""

    status: Literal["ready", "not_ready"]
    app: str
    version: str
    phase: int
    environment: str
    checks: list[DependencyStatus]
