"""Document upload, listing, and lifecycle management."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings, get_settings
from app.core.deps import UnitOfWork
from app.core.logging import get_logger
from app.db.enums import AnalyticsEventType, DocumentScope, DocumentStatus
from app.db.models.document import Document
from app.db.models.user import User
from app.schemas.documents import UrlIngestRequest
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.indexing import IndexService
from app.services.organizations import OrganizationService
from app.utils.files import (
    build_storage_path,
    read_upload_limited,
    sanitize_filename,
    sha256_bytes,
    sha256_file,
    validate_upload_file,
)
from app.utils.queue import enqueue_ingest

logger = get_logger(__name__)


class DocumentService:
    """Use cases for knowledge-base documents."""

    def __init__(self, uow: UnitOfWork, settings: Settings | None = None) -> None:
        self.uow = uow
        self.settings = settings or get_settings()

    async def upload_files(
        self,
        user: User,
        files: list[UploadFile],
        *,
        organization_id: str | None = None,
    ) -> list[Document]:
        if not files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided.")
        await self._validate_organization_scope(user, organization_id)
        created: list[Document] = []
        for upload in files:
            validate_upload_file(upload, self.settings)
            created.append(
                await self._create_from_bytes(
                    user=user,
                    filename=upload.filename or "upload.bin",
                    content_type=upload.content_type,
                    data=await read_upload_limited(upload, self.settings),
                    organization_id=organization_id,
                )
            )
        return created

    async def ingest_url(
        self,
        user: User,
        payload: UrlIngestRequest,
        *,
        organization_id: str | None = None,
    ) -> Document:
        await self._validate_organization_scope(user, organization_id)
        url = str(payload.url)
        title = payload.title or url
        content_hash = sha256_bytes(url.encode("utf-8"))
        document = await self._resolve_document_record(
            user=user,
            title=title,
            filename=Path(url).name or "webpage.html",
            content_type="text/html",
            extension="html",
            content_hash=content_hash,
            file_size_bytes=0,
            storage_path="",
            organization_id=organization_id,
            source_url=url,
        )
        await self._schedule_ingest(document.id)
        await self.uow.session.refresh(document)
        return document

    async def list_documents(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
        organization_id: str | None = None,
    ) -> tuple[list[Document], int]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size
        if organization_id:
            await OrganizationService(self.uow).require_membership(user, organization_id)
            items = await self.uow.documents.list_for_organization(
                organization_id,
                offset=offset,
                limit=page_size,
            )
            total = await self.uow.documents.count_for_organization(organization_id)
        else:
            items = await self.uow.documents.list_personal(
                user.id,
                offset=offset,
                limit=page_size,
            )
            total = await self.uow.documents.count_personal(user.id)
        return items, total

    async def get_document(self, user: User, document_id: str) -> Document:
        document = await self._get_owned_document(user, document_id)
        return document

    async def get_document_content(self, user: User, document_id: str) -> tuple[Document, str]:
        document = await self.uow.documents.get_with_chunks(document_id)
        if not document or not await self._can_read_document(user, document):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        if document.status == DocumentStatus.DELETED.value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        text = "\n\n".join(chunk.content for chunk in document.chunks)
        return document, text

    async def get_document_file(self, user: User, document_id: str) -> tuple[Document, Path]:
        document = await self._get_owned_document(user, document_id)
        path = Path(document.storage_path)
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found.")
        return document, path

    async def delete_document(self, user: User, document_id: str) -> None:
        document = await self._get_manageable_document(user, document_id)
        await IndexService(self.uow, self.settings).purge_document_vectors(document)
        document.status = DocumentStatus.DELETED.value
        await self.uow.session.flush()
        await self.uow.audit_logs.record(
            actor_id=user.id,
            action="document.delete",
            resource_type="document",
            resource_id=document.id,
        )

    async def _create_from_bytes(
        self,
        *,
        user: User,
        filename: str,
        content_type: str | None,
        data: bytes,
        organization_id: str | None,
        source_url: str | None = None,
    ) -> Document:
        from app.utils.files import file_extension

        ext = file_extension(filename)
        if not ext or ext not in self.settings.allowed_extension_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '.{ext or 'unknown'}' is not allowed.",
            )

        content_hash = sha256_bytes(data)
        title = sanitize_filename(filename)

        # Create placeholder to get id for storage path
        document = Document(
            owner_id=user.id,
            organization_id=organization_id,
            title=title,
            original_filename=filename,
            content_type=content_type,
            extension=ext,
            storage_path="",
            file_size_bytes=len(data),
            content_hash=content_hash,
            scope=DocumentScope.ORGANIZATION.value if organization_id else DocumentScope.PERSONAL.value,
            status=DocumentStatus.PENDING.value,
            source_url=source_url,
        )
        document = await self.uow.documents.add(document)

        storage_path = build_storage_path(user.id, document.id, filename, self.settings)
        storage_path.write_bytes(data)
        document.storage_path = str(storage_path)
        document.content_hash = sha256_file(storage_path)

        document = await self._apply_versioning(user, document)
        await self.uow.session.flush()
        await self.uow.analytics.record(
            user_id=user.id,
            event_type=AnalyticsEventType.UPLOAD.value,
            name="document_uploaded",
            status="queued",
            meta={"document_id": document.id, "filename": filename},
        )
        await self._schedule_ingest(document.id)
        await self.uow.session.refresh(document)
        return document

    async def _resolve_document_record(
        self,
        *,
        user: User,
        title: str,
        filename: str,
        content_type: str | None,
        extension: str,
        content_hash: str,
        file_size_bytes: int,
        storage_path: str,
        organization_id: str | None,
        source_url: str | None,
    ) -> Document:
        document = Document(
            owner_id=user.id,
            organization_id=organization_id,
            title=title,
            original_filename=filename,
            content_type=content_type,
            extension=extension,
            storage_path=storage_path,
            file_size_bytes=file_size_bytes,
            content_hash=content_hash,
            scope=DocumentScope.ORGANIZATION.value if organization_id else DocumentScope.PERSONAL.value,
            status=DocumentStatus.PENDING.value,
            source_url=source_url,
        )
        document = await self.uow.documents.add(document)
        document = await self._apply_versioning(user, document)
        await self.uow.session.flush()
        return document

    async def _apply_versioning(self, user: User, document: Document) -> Document:
        existing = await self.uow.documents.find_by_hash(
            owner_id=user.id,
            content_hash=document.content_hash,
            organization_id=document.organization_id,
        )
        if existing and existing.id != document.id:
            document.version = existing.version + 1
            await IndexService(self.uow, self.settings).purge_document_vectors(existing)
            existing.status = DocumentStatus.DELETED.value
            await self.uow.session.flush()
        return document

    async def _get_owned_document(self, user: User, document_id: str) -> Document:
        document = await self.uow.documents.get_by_id(document_id)
        if not document or not await self._can_read_document(user, document):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        if document.status == DocumentStatus.DELETED.value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        return document

    async def _get_manageable_document(self, user: User, document_id: str) -> Document:
        document = await self.uow.documents.get_by_id(document_id)
        if not document or document.status == DocumentStatus.DELETED.value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        if document.owner_id == user.id:
            return document
        if document.organization_id and await OrganizationService(self.uow).can_manage_document(
            user, document
        ):
            return document
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    async def _can_read_document(self, user: User, document: Document) -> bool:
        if document.status == DocumentStatus.DELETED.value:
            return False
        if document.owner_id == user.id:
            return True
        if document.organization_id:
            membership = await self.uow.organizations.get_membership(document.organization_id, user.id)
            return membership is not None
        return False

    async def _validate_organization_scope(self, user: User, organization_id: str | None) -> None:
        if organization_id:
            await OrganizationService(self.uow).require_membership(user, organization_id)

    async def _schedule_ingest(self, document_id: str) -> None:
        queued = await enqueue_ingest(document_id)
        if not queued:
            logger.info("ingest_inline_fallback", document_id=document_id)
            await IngestionPipeline(self.uow).process_document(document_id)
