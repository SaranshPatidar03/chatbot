"""Document and chunk repositories."""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import DocumentStatus
from app.db.models.document import Document, DocumentChunk
from app.db.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_with_chunks(self, document_id: str) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks), selectinload(Document.tags))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_hash(
        self,
        *,
        owner_id: str,
        content_hash: str,
        organization_id: str | None = None,
    ) -> Document | None:
        stmt = select(Document).where(
            Document.owner_id == owner_id,
            Document.content_hash == content_hash,
            Document.status != DocumentStatus.DELETED.value,
        )
        if organization_id is None:
            stmt = stmt.where(Document.organization_id.is_(None))
        else:
            stmt = stmt.where(Document.organization_id == organization_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_personal(
        self,
        owner_id: str,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Document]:
        stmt: Select[tuple[Document]] = select(Document).where(
            Document.owner_id == owner_id,
            Document.organization_id.is_(None),
            Document.status != DocumentStatus.DELETED.value,
        )
        if status is not None:
            stmt = stmt.where(Document.status == status)
        stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_personal(self, owner_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Document)
            .where(
                Document.owner_id == owner_id,
                Document.organization_id.is_(None),
                Document.status != DocumentStatus.DELETED.value,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_for_organization(
        self,
        organization_id: str,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Document]:
        stmt: Select[tuple[Document]] = select(Document).where(
            Document.organization_id == organization_id,
            Document.status != DocumentStatus.DELETED.value,
        )
        if status is not None:
            stmt = stmt.where(Document.status == status)
        stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_organization(self, organization_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Document)
            .where(
                Document.organization_id == organization_id,
                Document.status != DocumentStatus.DELETED.value,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_for_owner(
        self,
        owner_id: str,
        *,
        organization_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Document]:
        stmt: Select[tuple[Document]] = select(Document).where(
            Document.owner_id == owner_id,
            Document.status != DocumentStatus.DELETED.value,
        )
        if organization_id is not None:
            stmt = stmt.where(Document.organization_id == organization_id)
        if status is not None:
            stmt = stmt.where(Document.status == status)
        stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids(self, document_ids: list[str]) -> list[Document]:
        if not document_ids:
            return []
        stmt = select(Document).where(Document.id.in_(document_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_owner(self, owner_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(Document)
            .where(
                Document.owner_id == owner_id,
                Document.status != DocumentStatus.DELETED.value,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def total_storage_bytes(self, owner_id: str) -> int:
        stmt = (
            select(func.coalesce(func.sum(Document.file_size_bytes), 0))
            .where(
                Document.owner_id == owner_id,
                Document.status != DocumentStatus.DELETED.value,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_platform(
        self,
        *,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Document]:
        stmt: Select[tuple[Document]] = select(Document)
        if status:
            stmt = stmt.where(Document.status == status)
        else:
            stmt = stmt.where(Document.status != DocumentStatus.DELETED.value)
        stmt = stmt.order_by(Document.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_platform(self, *, status: str | None = None) -> int:
        stmt = select(func.count()).select_from(Document)
        if status:
            stmt = stmt.where(Document.status == status)
        else:
            stmt = stmt.where(Document.status != DocumentStatus.DELETED.value)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def platform_storage_summary(self) -> dict[str, int | dict[str, int]]:
        total_stmt = select(func.coalesce(func.sum(Document.file_size_bytes), 0)).where(
            Document.status != DocumentStatus.DELETED.value,
        )
        total_result = await self.session.execute(total_stmt)
        total_bytes = int(total_result.scalar_one())

        status_stmt = (
            select(Document.status, func.count())
            .where(Document.status != DocumentStatus.DELETED.value)
            .group_by(Document.status)
        )
        status_result = await self.session.execute(status_stmt)
        by_status = {row[0]: int(row[1]) for row in status_result.all()}
        return {"total_bytes": total_bytes, "by_status": by_status}


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    model = DocumentChunk

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_for_document(self, document_id: str) -> list[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_for_document(self, document_id: str) -> None:
        chunks = await self.list_for_document(document_id)
        for chunk in chunks:
            await self.session.delete(chunk)
        await self.session.flush()
