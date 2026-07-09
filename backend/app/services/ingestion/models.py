"""In-memory structures produced by document extractors."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ExtractedPage:
    """Text extracted from a single page or logical section."""

    text: str
    page_number: int | None = None


@dataclass(slots=True)
class ExtractedDocument:
    """Normalized extraction output for any supported source."""

    pages: list[ExtractedPage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(page.text.strip() for page in self.pages if page.text and page.text.strip())

    @property
    def page_count(self) -> int:
        numbered = [p.page_number for p in self.pages if p.page_number is not None]
        return max(numbered) if numbered else max(len(self.pages), 1)
