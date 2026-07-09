"""Dashboard summary API routes."""

from fastapi import APIRouter, Depends

from app.api.auth_deps import get_current_user
from app.core.deps import UnitOfWork, get_uow
from app.db.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> DashboardSummaryResponse:
    """Return document, chat, and storage overview for the current user."""
    return await DashboardService(uow).summary(current_user)
