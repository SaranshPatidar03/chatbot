"""VectorStore adapter unit tests."""

from unittest.mock import MagicMock

from app.db.enums import DocumentScope
from app.db.models.document import Document, DocumentChunk
from app.embeddings.store import VectorStore


def test_collection_name_for_personal_document() -> None:
    store = VectorStore()
    document = Document(
        owner_id="user-abc",
        title="Notes",
        original_filename="notes.txt",
        storage_path="/tmp/notes.txt",
        file_size_bytes=1,
        content_hash="abc",
        scope=DocumentScope.PERSONAL.value,
    )
    assert store.collection_name_for_document(document) == "kb_user-abc"


def test_collection_name_for_org_document() -> None:
    store = VectorStore()
    document = Document(
        owner_id="user-abc",
        organization_id="org-xyz",
        title="Notes",
        original_filename="notes.txt",
        storage_path="/tmp/notes.txt",
        file_size_bytes=1,
        content_hash="abc",
        scope=DocumentScope.ORGANIZATION.value,
    )
    assert store.collection_name_for_document(document) == "kb_org_org-xyz"


def test_upsert_chunks_calls_chroma_collection() -> None:
    store = VectorStore()
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    store._client = mock_client

    document = Document(
        id="doc-1",
        owner_id="user-1",
        title="Doc",
        original_filename="doc.txt",
        storage_path="/tmp/doc.txt",
        file_size_bytes=1,
        content_hash="hash",
        scope=DocumentScope.PERSONAL.value,
    )
    chunk = DocumentChunk(
        id="chunk-1",
        document_id="doc-1",
        chunk_index=0,
        content="hello",
    )

    store.upsert_chunks("kb_user-1", document, [chunk], [[0.1, 0.2]])

    mock_client.get_or_create_collection.assert_called_once_with(
        name="kb_user-1",
        metadata={"hnsw:space": "cosine"},
    )
    mock_collection.upsert.assert_called_once()
    kwargs = mock_collection.upsert.call_args.kwargs
    assert kwargs["ids"] == ["chunk-1"]
    assert kwargs["embeddings"] == [[0.1, 0.2]]
    assert kwargs["documents"] == ["hello"]
    assert kwargs["metadatas"][0]["document_id"] == document.id


def test_delete_document_vectors_uses_metadata_filter() -> None:
    store = VectorStore()
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_collection.return_value = mock_collection
    store._client = mock_client

    document = Document(
        id="doc-1",
        owner_id="user-1",
        title="Doc",
        original_filename="doc.txt",
        storage_path="/tmp/doc.txt",
        file_size_bytes=1,
        content_hash="hash",
        scope=DocumentScope.PERSONAL.value,
    )

    store.delete_document_vectors(document)

    mock_client.get_collection.assert_called_once_with(name="kb_user-1")
    mock_collection.delete.assert_called_once_with(where={"document_id": "doc-1"})
