"""Investigation persistence queries."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersentinel.db.models import Investigation, Report


class InvestigationRepository:
    """Read/write operations for investigations and reports."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, investigation_id: str) -> Investigation | None:
        statement = (
            select(Investigation)
            .where(Investigation.id == investigation_id)
            .options(selectinload(Investigation.reports))
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def get_active_for_incident(self, incident_id: str) -> Investigation | None:
        statement = (
            select(Investigation)
            .where(
                Investigation.incident_id == incident_id,
                Investigation.status.in_(["queued", "running"]),
            )
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def get_latest_report(self, investigation_id: str) -> Report | None:
        statement = (
            select(Report)
            .where(Report.investigation_id == investigation_id)
            .order_by(Report.version.desc())
            .limit(1)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()
