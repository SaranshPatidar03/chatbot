"""Per-user LLM / RAG settings API routes."""

from fastapi import APIRouter, Depends

from app.api.auth_deps import get_current_user
from app.core.deps import UnitOfWork, get_uow
from app.db.models.user import User
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdateRequest
from app.services.user_settings import UserSettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserSettingsResponse:
    """Return the current user's model and RAG preferences."""
    return await UserSettingsService(uow).get_settings(current_user)


@router.patch("", response_model=UserSettingsResponse)
async def update_user_settings(
    payload: UserSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> UserSettingsResponse:
    """Update model and RAG preferences for the current user."""
    return await UserSettingsService(uow).update_settings(current_user, payload)
