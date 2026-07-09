"""Per-user LLM / RAG settings."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class UserSettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User preferences for providers, generation, and RAG."""

    __tablename__ = "settings"

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    theme: Mapped[str] = mapped_column(String(16), default="system", nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(32), default="ollama", nullable=False)
    llm_model: Mapped[str] = mapped_column(String(128), default="llama3", nullable=False)
    embedding_provider: Mapped[str] = mapped_column(String(32), default="ollama", nullable=False)
    embedding_model: Mapped[str] = mapped_column(
        String(128),
        default="nomic-embed-text",
        nullable=False,
    )
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    top_p: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    allow_general_knowledge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.35, nullable=False)
    mmr_lambda: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    user: Mapped["User"] = relationship(back_populates="settings")
