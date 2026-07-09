"""Shared API dependencies — re-exported from ``app.core.deps``."""

from app.core.deps import (
    UnitOfWork,
    build_uow,
    get_app_settings,
    get_db,
    get_default_embeddings,
    get_default_llm,
    get_uow,
    get_vector_store,
)

__all__ = [
    "UnitOfWork",
    "build_uow",
    "get_app_settings",
    "get_db",
    "get_default_embeddings",
    "get_default_llm",
    "get_uow",
    "get_vector_store",
]
