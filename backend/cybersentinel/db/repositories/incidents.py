"""Incident persistence queries."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersentinel.db.models import Alert, Evidence, Incident, Investigation, Report, Review
from cybersentinel.utils.time import to_utc_second


def encode_cursor(created_at: datetime, incident_id: str) -> str:
    raw = f"{to_utc_second(created_at).isoformat()}|{incident_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    padding = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(cursor + padding).decode("utf-8")
        timestamp_text, identifier = raw.split("|", 1)
        return datetime.fromisoformat(timestamp_text), identifier
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        raise ValueError("invalid cursor") from exc


class IncidentRepository:
    """Read/write operations for incidents, evidence, reviews and reports."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, incident_id: str) -> Incident | None:
        statement = (
            select(Incident)
            .where(Incident.id == incident_id)
            .options(
                selectinload(Incident.alert).selectinload(Alert.event),
                selectinload(Incident.investigations).selectinload(Investigation.reports),
                selectinload(Incident.reviews),
            )
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def get_by_alert_id(self, alert_id: object) -> Incident | None:
        statement = (
            select(Incident)
            .where(Incident.alert_id == alert_id)
            .options(
                selectinload(Incident.alert).selectinload(Alert.event),
                selectinload(Incident.investigations),
                selectinload(Incident.reviews),
            )
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def list(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> tuple[list[Incident], str | None]:
        statement = select(Incident).order_by(
            desc(Incident.risk_score), desc(Incident.created_at)
        )
        if status:
            statement = statement.where(Incident.status == status)
        if severity:
            statement = statement.where(Incident.severity == severity)
        if cursor:
            cursor_time, cursor_id = decode_cursor(cursor)
            statement = statement.where(
                (Incident.created_at < cursor_time)
                | ((Incident.created_at == cursor_time) & (Incident.id < cursor_id))
            )

        statement = statement.limit(limit + 1)
        rows = (await self.session.execute(statement)).scalars().all()
        has_next = len(rows) > limit
        items = list(rows[:limit])
        next_cursor = None
        if has_next and items:
            last = items[-1]
            next_cursor = encode_cursor(last.created_at, last.id)
        return items, next_cursor

    async def get_evidence_for_incident(
        self, incident_id: str, kind: str | None = None
    ) -> list[Evidence]:
        statement = (
            select(Evidence)
            .join(Investigation, Evidence.investigation_id == Investigation.id)
            .where(Investigation.incident_id == incident_id)
            .order_by(Evidence.captured_at.asc())
        )
        if kind:
            statement = statement.where(Evidence.kind == kind)
        return list((await self.session.execute(statement)).scalars().all())

    async def add_review(self, review: Review) -> None:
        self.session.add(review)

    async def add_investigation(self, investigation: Investigation) -> None:
        self.session.add(investigation)

    async def add_report(self, report: Report) -> None:
        self.session.add(report)

    async def add_evidence(self, evidence: Evidence) -> None:
        self.session.add(evidence)
