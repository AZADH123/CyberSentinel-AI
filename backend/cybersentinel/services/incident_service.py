"""Incident read service."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cybersentinel.core.errors import NotFoundError
from cybersentinel.db.repositories.incidents import IncidentRepository
from cybersentinel.schemas.incident import EvidenceItem, IncidentDetail, IncidentSummary

logger = logging.getLogger(__name__)


class IncidentService:
    """Incident query projections."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = IncidentRepository(session)

    async def list_incidents(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
        status: str | None = None,
        severity: str | None = None,
    ) -> tuple[list[IncidentSummary], str | None]:
        incidents, next_cursor = await self.repo.list(
            limit=limit, cursor=cursor, status=status, severity=severity
        )
        summaries = [
            IncidentSummary(
                incident_id=inc.id,
                status=inc.status,  # type: ignore[arg-type]
                severity=inc.severity,  # type: ignore[arg-type]
                risk_score=inc.risk_score,
                risk_band=inc.risk_band,  # type: ignore[arg-type]
                confidence=inc.confidence,  # type: ignore[arg-type]
                created_at=inc.created_at,
            )
            for inc in incidents
        ]
        return summaries, next_cursor

    async def get_incident(self, incident_id: str) -> IncidentDetail:
        incident = await self.repo.get(incident_id)
        if incident is None:
            raise NotFoundError("incident", incident_id)

        alert_summary = None
        if incident.alert:
            event = incident.alert.event
            alert_summary = {
                "alert_id": str(incident.alert.id),
                "source": incident.alert.source,
                "event_type": incident.alert.event_type,
                "event_time": incident.alert.event_time.isoformat(),
                "username": event.username if event else None,
                "host": event.host if event else None,
                "source_ip": event.source_ip if event else None,
                "outcome": event.outcome if event else None,
                "failure_count": event.failure_count if event else 0,
            }

        latest_inv_id = None
        latest_inv_status = None
        latest_report = None
        if incident.investigations:
            latest = sorted(
                incident.investigations, key=lambda i: i.created_at, reverse=True
            )[0]
            latest_inv_id = latest.id
            latest_inv_status = latest.status
            if latest.reports:
                latest_report = sorted(
                    latest.reports, key=lambda r: r.version, reverse=True
                )[0].content

        reviews_data = [
            {
                "id": str(rev.id),
                "reviewer": rev.reviewer,
                "disposition": rev.disposition,
                "notes": rev.notes,
                "reviewed_at": rev.reviewed_at.isoformat(),
            }
            for rev in (incident.reviews or [])
        ]

        return IncidentDetail(
            incident_id=incident.id,
            alert_id=str(incident.alert_id),
            status=incident.status,  # type: ignore[arg-type]
            severity=incident.severity,  # type: ignore[arg-type]
            risk_score=incident.risk_score,
            risk_band=incident.risk_band,  # type: ignore[arg-type]
            confidence=incident.confidence,  # type: ignore[arg-type]
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            alert_summary=alert_summary,
            latest_investigation_id=latest_inv_id,
            investigation_status=latest_inv_status,
            report=latest_report,
            reviews=reviews_data,
        )

    async def get_evidence(
        self, incident_id: str, kind: str | None = None
    ) -> list[EvidenceItem]:
        incident = await self.repo.get(incident_id)
        if incident is None:
            raise NotFoundError("incident", incident_id)

        rows = await self.repo.get_evidence_for_incident(incident_id, kind=kind)
        return [
            EvidenceItem(
                id=str(row.id),
                investigation_id=row.investigation_id,
                evidence_key=row.evidence_key,
                kind=row.kind,
                source=row.source,
                reference=row.reference,
                captured_at=row.captured_at,
                value=row.value,
                checksum=row.checksum,
                supersedes=str(row.supersedes) if row.supersedes else None,
            )
            for row in rows
        ]
