"""ARQ job: ingest a document by id."""

from app.core.deps import build_uow
from app.core.logging import get_logger
from app.services.ingestion.pipeline import IngestionPipeline
from app.workers.db import get_worker_session_factory

logger = get_logger(__name__)


async def ingest_document(_ctx: dict, document_id: str) -> str:
    """Extract, chunk, and persist document text."""
    session_factory = get_worker_session_factory()
    async with session_factory() as session:
        uow = build_uow(session)
        try:
            document = await IngestionPipeline(uow).process_document(document_id)
            await session.commit()
            logger.info("worker_ingest_complete", document_id=document.id, status=document.status)
            return document.status
        except Exception:
            await session.rollback()
            raise
