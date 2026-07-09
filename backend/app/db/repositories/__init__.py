"""Repository pattern — shared base and concrete data-access classes."""

from app.db.repositories.analytics import AnalyticsRepository, AuditLogRepository
from app.db.repositories.base import BaseRepository
from app.db.repositories.chat import ChatRepository, MessageRepository
from app.db.repositories.document import DocumentChunkRepository, DocumentRepository
from app.db.repositories.organization import OrganizationRepository
from app.db.repositories.session import (
    EmailVerificationRepository,
    PasswordResetRepository,
    SessionRepository,
)
from app.db.repositories.settings import SettingsRepository
from app.db.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "OrganizationRepository",
    "SessionRepository",
    "PasswordResetRepository",
    "EmailVerificationRepository",
    "DocumentRepository",
    "DocumentChunkRepository",
    "ChatRepository",
    "MessageRepository",
    "SettingsRepository",
    "AuditLogRepository",
    "AnalyticsRepository",
]
