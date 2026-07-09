"""Domain enumerations shared across models and schemas."""

from enum import StrEnum


class PlatformRole(StrEnum):
    """Global application role."""

    USER = "user"
    PLATFORM_ADMIN = "platform_admin"


class OrgRole(StrEnum):
    """Role within an organization workspace."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class DocumentScope(StrEnum):
    """Where a document's knowledge lives."""

    PERSONAL = "personal"
    ORGANIZATION = "organization"


class DocumentStatus(StrEnum):
    """Ingestion / embedding lifecycle."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class ChunkKind(StrEnum):
    """Parent-child retrieval hierarchy."""

    PARENT = "parent"
    CHILD = "child"


class MessageRole(StrEnum):
    """Chat message author role."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AnalyticsEventType(StrEnum):
    """High-level analytics event categories."""

    REQUEST = "request"
    LLM_CALL = "llm_call"
    EMBEDDING = "embedding"
    RETRIEVAL = "retrieval"
    UPLOAD = "upload"
    AUTH = "auth"
    ERROR = "error"
