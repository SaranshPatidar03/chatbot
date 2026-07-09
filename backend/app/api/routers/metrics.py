"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Response

from app.core.metrics import metrics_payload

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """Expose Prometheus metrics for scraping."""
    body, content_type = metrics_payload()
    return Response(content=body, media_type=content_type)
