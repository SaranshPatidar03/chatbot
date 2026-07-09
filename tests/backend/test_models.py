"""ORM metadata and model registry tests."""

from app.db.models import (
    AnalyticsEvent,
    AuditLog,
    Base,
    Chat,
    Document,
    DocumentChunk,
    DocumentTag,
    Message,
    Organization,
    OrganizationMember,
    PasswordResetToken,
    Tag,
    User,
    UserSession,
    UserSettings,
)


EXPECTED_TABLES = {
    "users",
    "organizations",
    "organization_members",
    "sessions",
    "password_reset_tokens",
    "documents",
    "document_chunks",
    "tags",
    "document_tags",
    "chats",
    "messages",
    "settings",
    "audit_logs",
    "analytics_events",
}


def test_all_phase2_tables_registered() -> None:
    assert EXPECTED_TABLES.issubset(set(Base.metadata.tables))


def test_model_class_table_names() -> None:
    assert User.__tablename__ == "users"
    assert Organization.__tablename__ == "organizations"
    assert OrganizationMember.__tablename__ == "organization_members"
    assert UserSession.__tablename__ == "sessions"
    assert PasswordResetToken.__tablename__ == "password_reset_tokens"
    assert Document.__tablename__ == "documents"
    assert DocumentChunk.__tablename__ == "document_chunks"
    assert Tag.__tablename__ == "tags"
    assert DocumentTag.__tablename__ == "document_tags"
    assert Chat.__tablename__ == "chats"
    assert Message.__tablename__ == "messages"
    assert UserSettings.__tablename__ == "settings"
    assert AuditLog.__tablename__ == "audit_logs"
    assert AnalyticsEvent.__tablename__ == "analytics_events"
