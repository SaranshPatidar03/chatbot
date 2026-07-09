"""Audit and analytics repositories."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AnalyticsEvent, AuditLog
from app.db.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_recent(self, *, offset: int = 0, limit: int = 100) -> list[AuditLog]:
        stmt: Select[tuple[AuditLog]] = (
            select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_filtered(
        self,
        *,
        action: str | None = None,
        actor_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        stmt: Select[tuple[AuditLog]] = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        action: str | None = None,
        actor_id: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def record(
        self,
        *,
        action: str,
        actor_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        row = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
        return await self.add(row)


class AnalyticsRepository(BaseRepository[AnalyticsEvent]):
    model = AnalyticsEvent

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def record(
        self,
        *,
        event_type: str,
        name: str,
        user_id: str | None = None,
        duration_ms: float | None = None,
        token_count: int | None = None,
        status: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> AnalyticsEvent:
        row = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            name=name,
            duration_ms=duration_ms,
            token_count=token_count,
            status=status,
            meta=meta or {},
        )
        return await self.add(row)

    async def list_for_user(
        self,
        user_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AnalyticsEvent]:
        stmt = (
            select(AnalyticsEvent)
            .where(AnalyticsEvent.user_id == user_id)
            .order_by(AnalyticsEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_admin(
        self,
        *,
        event_type: str | None = None,
        user_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AnalyticsEvent]:
        stmt = select(AnalyticsEvent)
        if event_type:
            stmt = stmt.where(AnalyticsEvent.event_type == event_type)
        if user_id:
            stmt = stmt.where(AnalyticsEvent.user_id == user_id)
        stmt = stmt.order_by(AnalyticsEvent.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_admin(
        self,
        *,
        event_type: str | None = None,
        user_id: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(AnalyticsEvent)
        if event_type:
            stmt = stmt.where(AnalyticsEvent.event_type == event_type)
        if user_id:
            stmt = stmt.where(AnalyticsEvent.user_id == user_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def summarize(self, *, days: int = 7) -> dict[str, Any]:
        since = datetime.now(UTC) - timedelta(days=max(days, 1))

        type_stmt = (
            select(AnalyticsEvent.event_type, func.count())
            .where(AnalyticsEvent.created_at >= since)
            .group_by(AnalyticsEvent.event_type)
        )
        type_result = await self.session.execute(type_stmt)
        by_type = {row[0]: int(row[1]) for row in type_result.all()}

        llm_stmt = select(
            func.count(),
            func.coalesce(func.avg(AnalyticsEvent.duration_ms), 0),
            func.coalesce(func.sum(AnalyticsEvent.token_count), 0),
        ).where(
            AnalyticsEvent.created_at >= since,
            AnalyticsEvent.event_type == "llm_call",
        )
        llm_result = await self.session.execute(llm_stmt)
        llm_count, llm_avg_ms, llm_tokens = llm_result.one()

        total_result = await self.session.execute(
            select(func.count()).where(AnalyticsEvent.created_at >= since)
        )
        total_events = int(total_result.scalar_one())

        return {
            "days": days,
            "total_events": total_events,
            "by_type": by_type,
            "llm_calls": int(llm_count or 0),
            "llm_avg_latency_ms": round(float(llm_avg_ms or 0), 2),
            "llm_total_tokens": int(llm_tokens or 0),
        }
