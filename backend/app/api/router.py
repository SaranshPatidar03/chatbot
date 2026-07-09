"""API routers."""

from fastapi import APIRouter

from app.api.routers import (
    admin,
    auth,
    chat,
    dashboard,
    documents,
    health,
    organizations,
    search,
    settings,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(settings.router)
api_router.include_router(dashboard.router)
api_router.include_router(organizations.router)
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(chat.router)
api_router.include_router(admin.router)
