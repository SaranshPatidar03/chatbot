"""Unit of Work and DI wiring tests."""

from unittest.mock import MagicMock

from app.core.deps import UnitOfWork, build_uow
from app.db.enums import DocumentScope, DocumentStatus, OrgRole, PlatformRole


def test_build_uow_exposes_all_repositories() -> None:
    session = MagicMock()
    uow = build_uow(session)
    assert isinstance(uow, UnitOfWork)
    assert uow.session is session
    assert uow.users.session is session
    assert uow.organizations.session is session
    assert uow.documents.session is session
    assert uow.chats.session is session
    assert uow.settings.session is session
    assert uow.audit_logs.session is session
    assert uow.analytics.session is session


def test_domain_enums() -> None:
    assert PlatformRole.USER == "user"
    assert PlatformRole.PLATFORM_ADMIN == "platform_admin"
    assert OrgRole.OWNER == "owner"
    assert DocumentScope.PERSONAL == "personal"
    assert DocumentStatus.READY == "ready"
