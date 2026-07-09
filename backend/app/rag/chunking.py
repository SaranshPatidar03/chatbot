"""Chunking strategies — recursive / parent-child (Phase 6–7)."""

from dataclasses import dataclass


@dataclass(slots=True)
class TextChunk:
    """In-memory chunk before persistence / embedding."""

    content: str
    chunk_index: int
    parent_index: int | None = None
    page_number: int | None = None
    metadata: dict | None = None


def recursive_split(
    text: str,
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: list[str] | None = None,
) -> list[str]:
    """Split text recursively using a separator hierarchy.

    Full parent-child indexing is completed in the embeddings phase.
    """
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    seps = separators or ["\n\n", "\n", ". ", " ", ""]
    separator = seps[0]
    remaining_seps = seps[1:] if len(seps) > 1 else [""]

    if separator:
        parts = text.split(separator)
    else:
        parts = list(text)

    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = current + (separator if current else "") + part if separator else current + part
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(part) > chunk_size and remaining_seps:
            chunks.extend(
                recursive_split(
                    part,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=remaining_seps,
                )
            )
            current = ""
        else:
            current = part

    if current:
        chunks.append(current)

    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    # Apply overlap by back-referencing previous chunk tails
    overlapped: list[str] = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = overlapped[-1][-chunk_overlap:]
        overlapped.append(prev_tail + chunks[i])
    return overlapped
