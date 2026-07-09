"""Knowledge search API routes."""

from fastapi import APIRouter, Depends

from app.api.auth_deps import get_current_user
from app.core.deps import UnitOfWork, get_uow
from app.db.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search_knowledge(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
) -> SearchResponse:
    """Search indexed knowledge with semantic, keyword, or hybrid retrieval."""
    return await SearchService(uow).search(current_user, payload)
