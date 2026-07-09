"""IndexService unit tests."""

from uuid import uuid4

import pytest

from app.core.deps import build_uow
from app.db.enums import DocumentScope, DocumentStatus
from app.db.models.document import Document, DocumentChunk
from app.services.indexing import IndexService
from fakes import FakeEmbeddingProvider, InMemoryVectorStore


@pytest.mark.asyncio
async def test_index_chunks_sets_chroma_metadata(db_session) -> None:
    uow = build_uow(db_session)
    store = InMemoryVectorStore()
    provider = FakeEmbeddingProvider(dimensions=4)
    owner_id = str(uuid4())

    document = Document(
        owner_id=owner_id,
        title="Policy",
        original_filename="policy.txt",
        content_type="text/plain",
        extension="txt",
        storage_path="/tmp/policy.txt",
        file_size_bytes=10,
        content_hash="hash-1",
        scope=DocumentScope.PERSONAL.value,
        status=DocumentStatus.PROCESSING.value,
    )
    document = await uow.documents.add(document)

    chunks = [
        DocumentChunk(document_id=document.id, chunk_index=0, content="First chunk."),
        DocumentChunk(document_id=document.id, chunk_index=1, content="Second chunk."),
    ]
    for chunk in chunks:
        await uow.chunks.add(chunk)

    indexed = await IndexService(
        uow,
        vector_store=store,
        embedding_provider=provider,
    ).index_chunks(document, chunks)

    assert indexed == 2
    assert all(chunk.chroma_id == chunk.id for chunk in chunks)
    assert all(chunk.embedding_model == "fake-embedding-model" for chunk in chunks)
    assert store.count_for_document(document) == 2


@pytest.mark.asyncio
async def test_purge_document_vectors_removes_entries(db_session) -> None:
    uow = build_uow(db_session)
    store = InMemoryVectorStore()
    provider = FakeEmbeddingProvider()
    owner_id = str(uuid4())

    document = Document(
        owner_id=owner_id,
        title="Guide",
        original_filename="guide.txt",
        content_type="text/plain",
        extension="txt",
        storage_path="/tmp/guide.txt",
        file_size_bytes=10,
        content_hash="hash-2",
        scope=DocumentScope.PERSONAL.value,
        status=DocumentStatus.READY.value,
    )
    document = await uow.documents.add(document)
    chunk = DocumentChunk(document_id=document.id, chunk_index=0, content="Guide text.")
    await uow.chunks.add(chunk)

    service = IndexService(uow, vector_store=store, embedding_provider=provider)
    await service.index_chunks(document, [chunk])
    assert store.count_for_document(document) == 1

    await service.purge_document_vectors(document)
    assert store.count_for_document(document) == 0
