"""Tests for recursive chunking."""

from app.rag.chunking import recursive_split


def test_recursive_split_short_text() -> None:
    assert recursive_split("hello", chunk_size=100) == ["hello"]


def test_recursive_split_respects_size() -> None:
    text = ("Paragraph one. " * 40) + "\n\n" + ("Paragraph two. " * 40)
    chunks = recursive_split(text, chunk_size=120, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(isinstance(chunk, str) and chunk for chunk in chunks)
