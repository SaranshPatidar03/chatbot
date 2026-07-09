"""FastAPI application entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routers import health as health_router
from app.api.routers import metrics as metrics_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.core.redis import close_redis
from app.utils.files import ensure_storage_dirs

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application startup / shutdown hooks."""
    settings = get_settings()
    configure_logging(debug=settings.app_debug)
    ensure_storage_dirs()
    logger.info(
        "app_startup",
        app=settings.app_name,
        env=settings.app_env,
        api_prefix=settings.app_api_prefix,
    )
    try:
        yield
    finally:
        await close_redis()
        logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Grounded RAG chatbot API. Answers are derived only from the "
            "user-provided knowledge base unless general knowledge is explicitly enabled."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.app_api_prefix)
    application.include_router(health_router.router, tags=["health"])
    application.include_router(metrics_router.router)

    return application


app = create_app()
