"""Alert ingestion and read use cases.

The service owns the transaction boundary: one alert, its normalised event, its incident (or
duplicate link) and the audit record either all persist or none do.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from cybersentinel.core.errors import ConflictError, InvalidRequestError, NotFoundError
from cybersentinel.db.models import Alert, AuditLog, Event, Incident
from cybersentinel.db.repositories.alerts import AlertRepository
from cybersentinel.schemas.alert import AlertCreate
from cybersentinel.utils.ids import new_uuid7

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlertCreationResult:
    """Outcome of an idempotent alert creation attempt."""

    alert: Alert
    event: Event
    incident: Incident
    created: bool


class AlertService:
    """Coordinate alert persistence, idempotency and duplicate detection."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.alerts = AlertRepository(session)

    async def create_alert(
        self,
        payload: AlertCreate,
        *,
        idempotency_header: str | None,
        correlation_id: str,
        actor: str = "system:ingest",
    ) -> AlertCreationResult:
        """Create or replay an alert.

        Idempotency header takes precedence over the body key. A key replayed with identical
        content returns the original record; a key replayed with different content is a 409.
        """
        key = self._effective_idempotency_key(payload, idempotency_header)
        fingerprint = payload.request_fingerprint()

        async with self.session.begin():
            if key is not None:
                existing = await self.alerts.get_by_idempotency_key(key)
                if existing is not None:
                    if existing.request_fingerprint != fingerprint:
                        raise ConflictError(
                            "idempotency_key_conflict",
                            "Idempotency-Key was already used with different content",
                            [{"field": "Idempotency-Key", "issue": "content differs"}],
                        )
                    incident = self._resolve_incident(existing)
                    if existing.event is None:
                        raise RuntimeError("alert replay is missing its normalised event")
                    return AlertCreationResult(
                        alert=existing,
                        event=existing.event,
                        incident=incident,
                        created=False,
                    )

            original = await self.alerts.find_near_duplicate(payload)
            alert = Alert(
                id=new_uuid7(),
                source=payload.source,
                event_type=payload.event_type.value,
                event_time=payload.event_time,
                raw_event=payload.stored_raw_payload(),
                normalized_event=payload.normalized(),
                dedupe_hash=payload.dedupe_hash(),
                request_fingerprint=fingerprint,
                duplicate_of=original.id if original is not None else None,
                idempotency_key=key,
            )
            self.session.add(alert)
            await self.session.flush()

            event = Event(
                id=uuid.uuid4(),
                alert_id=alert.id,
                username=payload.username,
                host=payload.host,
                source_ip=payload.source_ip,
                action=payload.event_type.value,
                outcome=payload.outcome.value,
                event_time=payload.event_time,
                asset_criticality=payload.asset_criticality.value,
                failure_count=payload.failure_count or 0,
            )
            self.session.add(event)

            if original is not None:
                incident = self._resolve_incident(original)
                action = "alert.duplicate_linked"
                detail: dict[str, Any] = {"duplicate_of": str(original.id)}
            else:
                await self.alerts.lock_incident_sequence(payload.event_time.year)
                incident_id = await self.alerts.next_incident_id(payload.event_time.year)
                incident = Incident(
                    id=incident_id,
                    alert_id=alert.id,
                    status="open",
                    severity="informational",
                    risk_score=0,
                    risk_band="informational",
                    confidence="low",
                )
                self.session.add(incident)
                action = "alert.created"
                detail = {"event_type": payload.event_type.value}

            self.session.add(
                AuditLog(
                    actor=actor,
                    action=action,
                    entity_type="alert",
                    entity_id=str(alert.id),
                    outcome="success",
                    correlation_id=correlation_id,
                    detail=detail,
                )
            )
            await self.session.flush()
            logger.info(
                "alert persisted",
                extra={"event": action, "path": "/api/v1/alerts"},
            )
            return AlertCreationResult(
                alert=alert, event=event, incident=incident, created=True
            )

    async def get_alert(self, alert_id: uuid.UUID) -> tuple[Alert, Event, Incident]:
        """Return an alert with its event and effective incident, or raise 404."""
        alert = await self.alerts.get(alert_id)
        if alert is None or alert.event is None:
            raise NotFoundError("alert", str(alert_id))
        return alert, alert.event, self._resolve_incident(alert)

    async def list_alerts(
        self,
        *,
        limit: int,
        cursor: str | None,
        status: str | None,
        severity: str | None,
        source: str | None,
        from_time: datetime | None,
        to_time: datetime | None,
    ) -> tuple[list[tuple[Alert, Event, Incident]], str | None]:
        """Return a page of alert queue rows."""
        try:
            return await self.alerts.list(
                limit=limit,
                cursor=cursor,
                status=status,
                severity=severity,
                source=source,
                from_time=from_time,
                to_time=to_time,
            )
        except ValueError as exc:
            raise InvalidRequestError(
                "Invalid pagination cursor",
                details=[{"field": "cursor", "issue": "cursor is malformed or expired"}],
            ) from exc

    def _resolve_incident(self, alert: Alert) -> Incident:
        """Resolve the original incident for a duplicate alert."""
        if alert.incident is not None:
            return alert.incident
        if alert.duplicate_of_alert is not None and alert.duplicate_of_alert.incident is not None:
            return alert.duplicate_of_alert.incident
        raise RuntimeError(f"alert {alert.id} has no incident or duplicate origin")

    @staticmethod
    def _effective_idempotency_key(
        payload: AlertCreate, header_value: str | None
    ) -> str | None:
        key = header_value.strip() if header_value is not None else payload.idempotency_key
        if key is None:
            return None
        if not 8 <= len(key) <= 128:
            raise InvalidRequestError(
                "Idempotency-Key must be 8-128 characters",
                details=[{"field": "Idempotency-Key", "issue": "length must be 8-128"}],
            )
        if any(ord(char) < 32 or ord(char) == 127 for char in key):
            raise InvalidRequestError(
                "Idempotency-Key contains control characters",
                details=[{"field": "Idempotency-Key", "issue": "control characters rejected"}],
            )
        return key
