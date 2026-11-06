"""Alert persistence queries.

Every SQL statement in the application lives in this repository layer. The service layer
never constructs a query, which keeps transaction logic testable and SQL reviewable.
"""

from __future__ import annotations

import base64
import binascii
import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cybersentinel.core.constants import NEAR_DUPLICATE_WINDOW_SECONDS
from cybersentinel.db.models import Alert, Event, Incident
from cybersentinel.schemas.alert import AlertCreate
from cybersentinel.utils.ids import parse_incident_sequence
from cybersentinel.utils.time import to_utc_second


def encode_cursor(created_at: datetime, alert_id: uuid.UUID) -> str:
    """Encode a stable creation-time cursor without exposing a raw offset."""
    raw = f"{to_utc_second(created_at).isoformat()}|{alert_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Decode a cursor, raising ``ValueError`` for malformed input."""
    padding = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(cursor + padding).decode("utf-8")
        timestamp_text, identifier = raw.split("|", 1)
        return datetime.fromisoformat(timestamp_text), uuid.UUID(identifier)
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        raise ValueError("invalid cursor") from exc


class AlertRepository:
    """Read/write operations for alerts, events and their incidents."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_idempotency_key(self, key: str) -> Alert | None:
        """Return an alert previously stored for an idempotency key."""
        statement = (
            select(Alert)
            .where(Alert.idempotency_key == key)
            .options(
                selectinload(Alert.event),
                selectinload(Alert.incident),
                selectinload(Alert.duplicate_of_alert).selectinload(Alert.incident),
            )
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def get(self, alert_id: uuid.UUID) -> Alert | None:
        """Return an alert with its event and incident projection."""
        statement = (
            select(Alert)
            .where(Alert.id == alert_id)
            .options(
                selectinload(Alert.event),
                selectinload(Alert.incident),
                selectinload(Alert.duplicate_of_alert).selectinload(Alert.incident),
            )
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def find_near_duplicate(self, payload: AlertCreate) -> Alert | None:
        """Find an original alert with identical event dimensions within 60 seconds."""
        start = payload.event_time - timedelta(seconds=NEAR_DUPLICATE_WINDOW_SECONDS)
        end = payload.event_time + timedelta(seconds=NEAR_DUPLICATE_WINDOW_SECONDS)
        statement = (
            select(Alert)
            .join(Event, Event.alert_id == Alert.id)
            .where(
                Alert.duplicate_of.is_(None),
                Alert.source == payload.source,
                Alert.event_type == payload.event_type.value,
                Event.event_time.between(start, end),
                func.lower(Event.username) == payload.username.casefold(),
                Event.source_ip == payload.source_ip,
                Event.host == payload.host,
                Event.outcome == payload.outcome.value,
            )
            .options(selectinload(Alert.incident))
            .order_by(Event.event_time.asc())
            .limit(1)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def lock_incident_sequence(self, year: int) -> None:
        """Serialise incident-code allocation for a year inside the current transaction.

        The table-level sequence is intentionally not a database sequence because the PRD
        requires a human-readable yearly code and a bounded retry is simpler to audit.
        """
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"cybersentinel:incident:{year}"},
        )

    async def next_incident_id(self, year: int) -> str:
        """Allocate the next ``INC-YYYY-NNNN`` code after taking the advisory lock."""
        prefix = f"INC-{year}-"
        statement = (
            select(Incident.id)
            .where(Incident.id.like(f"{prefix}%"))
            .order_by(Incident.id.desc())
            .limit(1)
        )
        latest = (await self.session.execute(statement)).scalar_one_or_none()
        next_sequence = 1
        if latest is not None:
            parsed = parse_incident_sequence(latest, year)
            next_sequence = (parsed or 0) + 1
        if next_sequence > 9999:
            raise OverflowError(f"incident sequence exhausted for {year}")
        return f"{prefix}{next_sequence:04d}"

    async def list(
        self,
        *,
        limit: int,
        cursor: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        source: str | None = None,
        from_time: datetime | None = None,
        to_time: datetime | None = None,
    ) -> tuple[list[tuple[Alert, Event, Incident]], str | None]:
        """List alert/event/incident triples newest-first with an opaque cursor."""
        statement = (
            select(Alert, Event, Incident)
            .join(Event, Event.alert_id == Alert.id)
            .join(Incident, Incident.alert_id == Alert.id)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .limit(limit + 1)
        )
        if status is not None:
            statement = statement.where(Incident.status == status)
        if severity is not None:
            statement = statement.where(Incident.severity == severity)
        if source is not None:
            statement = statement.where(Alert.source == source)
        if from_time is not None:
            statement = statement.where(Alert.event_time >= from_time)
        if to_time is not None:
            statement = statement.where(Alert.event_time <= to_time)
        if cursor is not None:
            cursor_time, cursor_id = decode_cursor(cursor)
            statement = statement.where(
                or_(
                    Alert.created_at < cursor_time,
                    and_(Alert.created_at == cursor_time, Alert.id < cursor_id),
                )
            )

        rows = list((await self.session.execute(statement)).all())
        has_more = len(rows) > limit
        page = rows[:limit]
        next_cursor = None
        if has_more and page:
            last_alert = page[-1][0]
            next_cursor = encode_cursor(last_alert.created_at, last_alert.id)
        return page, next_cursor
