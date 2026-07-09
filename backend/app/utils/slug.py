"""URL slug helpers."""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str, *, max_length: int = 64) -> str:
    """Convert a human-readable name into a URL-safe slug."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^\w\s-]", "", ascii_text).strip().lower()
    slug = re.sub(r"[-\s]+", "-", cleaned).strip("-")
    if not slug:
        slug = "org"
    return slug[:max_length].rstrip("-")
