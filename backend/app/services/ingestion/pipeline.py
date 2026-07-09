"""Document ingestion pipeline — extract, clean, chunk, embed, persist."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.deps import UnitOfWork
from app.core.logging import get_logger
from app.db.enums import AnalyticsEventType, ChunkKind, DocumentStatus
from app.db.models.document import Document, DocumentChunk
from app.rag.chunking import recursive_split
from app.services.indexing import IndexService
from app.services.ingestion.extractors import extract_file, extract_url
from app.services.ingestion.models import ExtractedDocument

logger = get_logger(__name__)


class IngestionPipeline:
    """Parse documents into searchable text chunks and vector indexes."""

    def __init__(self, uow: UnitOfWork, settings: Settings | None = None) -> None:
        self.uow = uow
        self.settings = settings or get_settings()

    async def process_document(self, document_id: str) -> Document:
        document = await self.uow.documents.get_by_id(document_id)
        if not document or document.status == DocumentStatus.DELETED.value:
            raise ValueError(f"Document not found: {document_id}")

        document.status = DocumentStatus.PROCESSING.value
        document.error_message = None
        await self.uow.session.flush()

        started = datetime.now(UTC)
        try:
            extracted = await self._extract(document)
            await IndexService(self.uow, self.settings).purge_document_vectors(document)
            await self.uow.chunks.delete_for_document(document.id)
            chunk_count = await self._persist_chunks(document, extracted)
            chunks = await self.uow.chunks.list_for_document(document.id)
            await IndexService(self.uow, self.settings).index_chunks(document, chunks)

            document.page_count = extracted.page_count
            document.chunk_count = chunk_count
            document.status = DocumentStatus.READY.value
            document.processed_at = datetime.now(UTC)
            document.meta = {**document.meta, **extracted.metadata, "text_length": len(extracted.full_text)}
            await self.uow.session.flush()
            duration_ms = (datetime.now(UTC) - started).total_seconds() * 1000
            await self.uow.analytics.record(
                user_id=document.owner_id,
                event_type=AnalyticsEventType.UPLOAD.value,
                name="document_ingested",
                duration_ms=duration_ms,
                status="success",
                meta={"document_id": document.id, "chunks": chunk_count},
            )
            logger.info(
                "document_ingested",
                document_id=document.id,
                chunks=chunk_count,
                duration_ms=round(duration_ms, 2),
            )
            return document
        except Exception as exc:
            document.status = DocumentStatus.FAILED.value
            document.error_message = str(exc)
            await self.uow.session.flush()
            await self.uow.analytics.record(
                user_id=document.owner_id,
                event_type=AnalyticsEventType.ERROR.value,
                name="document_ingest_failed",
                status="failed",
                meta={"document_id": document.id, "error": str(exc)},
            )
            logger.exception("document_ingest_failed", document_id=document.id)
            raise

    async def _extract(self, document: Document) -> ExtractedDocument:
        if document.source_url:
            return await extract_url(document.source_url)
        path = Path(document.storage_path)
        if not path.exists():
            raise FileNotFoundError(f"Stored file missing: {document.storage_path}")
        return extract_file(path, extension=document.extension, content_type=document.content_type)

    async def _persist_chunks(self, document: Document, extracted: ExtractedDocument) -> int:
        chunk_size = self.settings.rag_chunk_size
        chunk_overlap = self.settings.rag_chunk_overlap
        index = 0

        if extracted.pages and any(p.text for p in extracted.pages):
            for page in extracted.pages:
                if not page.text.strip():
                    continue
                for piece in recursive_split(
                    page.text,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                ):
                    if not piece.strip():
                        continue
                    chunk = DocumentChunk(
                        document_id=document.id,
                        kind=ChunkKind.CHILD.value,
                        chunk_index=index,
                        content=piece,
                        page_number=page.page_number,
                        token_count=len(piece.split()),
                    )
                    await self.uow.chunks.add(chunk)
                    index += 1
        else:
            combined = extracted.full_text
            for piece in recursive_split(
                combined,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            ):
                if not piece.strip():
                    continue
                chunk = DocumentChunk(
                    document_id=document.id,
                    kind=ChunkKind.CHILD.value,
                    chunk_index=index,
                    content=piece,
                    token_count=len(piece.split()),
                )
                await self.uow.chunks.add(chunk)
                index += 1

        return index
