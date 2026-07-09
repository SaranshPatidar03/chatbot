"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.config import get_settings
from app.core.metrics import metrics_payload

router = APIRouter(tags=["metrics"])


async def _verify_metrics_access(request: Request) -> None:
    """Optional bearer token gate for ``/metrics`` in production."""
    settings = get_settings()
    if not settings.metrics_require_auth:
        return
    token = settings.metrics_scrape_token.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics scraping is disabled until METRICS_SCRAPE_TOKEN is configured.",
        )
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {token}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid metrics scrape credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/metrics", dependencies=[Depends(_verify_metrics_access)])
async def prometheus_metrics() -> Response:
    """Expose Prometheus metrics for scraping."""
    body, content_type = metrics_payload()
    return Response(content=body, media_type=content_type)
