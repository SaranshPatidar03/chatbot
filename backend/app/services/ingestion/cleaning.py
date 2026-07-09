"""Text normalization helpers."""

import re

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_SPACE = re.compile(r"[ \t]+")
_MULTI_NEWLINES = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """Remove control characters and collapse noisy whitespace."""
    if not text:
        return ""
    cleaned = _CONTROL_CHARS.sub("", text)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_MULTI_SPACE.sub(" ", line).strip() for line in cleaned.split("\n")]
    joined = "\n".join(line for line in lines if line)
    return _MULTI_NEWLINES.sub("\n\n", joined).strip()
