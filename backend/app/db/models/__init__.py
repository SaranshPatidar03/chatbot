"""ORM models package — import all models so Alembic sees metadata."""

from app.db.base import Base
from app.db.models.audit import AnalyticsEvent, AuditLog
from app.db.models.chat import Chat, Message
from app.db.models.document import Document, DocumentChunk
from app.db.models.organization import Organization, OrganizationMember
from app.db.models.session import PasswordResetToken, UserSession
from app.db.models.settings import UserSettings
from app.db.models.tag import DocumentTag, Tag
from app.db.models.user import User

__all__ = [
    "Base",
    "User",
    "Organization",
    "OrganizationMember",
    "UserSession",
    "PasswordResetToken",
    "Document",
    "DocumentChunk",
    "Tag",
    "DocumentTag",
    "Chat",
    "Message",
    "UserSettings",
    "AuditLog",
    "AnalyticsEvent",
]
