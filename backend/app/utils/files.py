"""Filesystem and hashing helpers."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings, get_settings

_UNSAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


def ensure_storage_dirs() -> None:
    """Create upload and temp directories if missing."""
    settings = get_settings()
    Path(settings.storage_path).mkdir(parents=True, exist_ok=True)
    Path(settings.temp_path).mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Return a safe basename for storage."""
    name = Path(filename).name
    cleaned = _UNSAFE_NAME.sub("_", name).strip("._")
    return cleaned or f"upload_{uuid4().hex[:8]}"


def file_extension(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def validate_upload_file(upload: UploadFile, settings: Settings | None = None) -> str:
    """Validate upload metadata and return normalized extension."""
    cfg = settings or get_settings()
    if not upload.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required.")
    ext = file_extension(upload.filename)
    if ext not in cfg.allowed_extension_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{ext}' is not allowed.",
        )
    return ext


async def read_upload_limited(upload: UploadFile, settings: Settings | None = None) -> bytes:
    """Read upload bytes enforcing configured max size."""
    cfg = settings or get_settings()
    chunks: list[bytes] = []
    total = 0
    while True:
        data = await upload.read(1024 * 1024)
        if not data:
            break
        total += len(data)
        if total > cfg.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {cfg.max_upload_size_mb} MB.",
            )
        chunks.append(data)
    return b"".join(chunks)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def user_document_dir(user_id: str, document_id: str, settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    return Path(cfg.storage_path) / user_id / document_id


def build_storage_path(user_id: str, document_id: str, filename: str, settings: Settings | None = None) -> Path:
    directory = user_document_dir(user_id, document_id, settings)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / sanitize_filename(filename)
