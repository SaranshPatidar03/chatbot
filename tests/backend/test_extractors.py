"""Extractor unit tests."""

from pathlib import Path

from app.services.ingestion.extractors import extract_file


def test_extract_txt(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("Hello knowledge base.\n\nSecond paragraph.", encoding="utf-8")
    doc = extract_file(path)
    assert "Hello knowledge base" in doc.full_text
    assert doc.page_count >= 1


def test_extract_json(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('{"policy": "20 days leave"}', encoding="utf-8")
    doc = extract_file(path)
    assert "20 days leave" in doc.full_text
