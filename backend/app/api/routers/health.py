"""Health and readiness endpoints."""

from fastapi import APIRouter, Response, status

from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.health import HealthService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe — process is up."""
    return HealthService().liveness()


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(response: Response) -> ReadinessResponse:
    """Readiness probe — Postgres, Redis, and Chroma availability."""
    result = await HealthService().readiness()
    if result.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
