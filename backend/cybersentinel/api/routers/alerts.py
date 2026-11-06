"""Alert ingestion and read endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status

from cybersentinel.api.deps import SessionDep
from cybersentinel.api.middleware.correlation import correlation_for_request
from cybersentinel.core.constants import IncidentStatus, Severity
from cybersentinel.core.errors import InvalidRequestError
from cybersentinel.db.models import Incident
from cybersentinel.schemas.alert import (
    AlertCreate,
    AlertCreateResponse,
    AlertDetail,
    AlertListItem,
    AlertListResponse,
    NormalizedEventView,
)
from cybersentinel.schemas.incident import IncidentSummary
from cybersentinel.services.alert_service import AlertService
from cybersentinel.utils.time import require_aware

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _incident_summary(incident: Incident) -> IncidentSummary:
    return IncidentSummary(
        incident_id=incident.id,
        status=incident.status,
        severity=incident.severity,
        risk_score=incident.risk_score,
        risk_band=incident.risk_band,
        confidence=incident.confidence,
        created_at=incident.created_at,
    )


@router.post(
    "",
    response_model=AlertCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an alert and its incident",
)
async def create_alert(
    payload: AlertCreate,
    request: Request,
    response: Response,
    session: SessionDep,
) -> AlertCreateResponse:
    """Persist a validated alert, normalised event, incident and audit record.

    A repeated Idempotency-Key with identical content returns HTTP 200 and the original IDs.
    """
    correlation_id = correlation_for_request(request)
    if correlation_id is None:
        raise RuntimeError("correlation middleware did not run")

    result = await AlertService(session).create_alert(
        payload,
        idempotency_header=request.headers.get("Idempotency-Key"),
        correlation_id=correlation_id,
    )
    if not result.created:
        response.status_code = status.HTTP_200_OK

    return AlertCreateResponse(
        alert_id=str(result.alert.id),
        incident_id=result.incident.id,
        status=result.incident.status,
        event_time=result.alert.event_time,
        created_at=result.alert.created_at,
        duplicate_of=(
            str(result.alert.duplicate_of) if result.alert.duplicate_of is not None else None
        ),
    )


@router.get("", response_model=AlertListResponse, summary="List alerts")
async def list_alerts(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
    incident_status: Annotated[IncidentStatus | None, Query(alias="status")] = None,
    severity: Severity | None = None,
    source: str | None = None,
    from_time: Annotated[datetime | None, Query(alias="from")] = None,
    to_time: Annotated[datetime | None, Query(alias="to")] = None,
) -> AlertListResponse:
    """Return the alert queue newest-first with opaque cursor pagination."""
    for field, value in (("from", from_time), ("to", to_time)):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise InvalidRequestError(
                "Query timestamps must include a timezone offset",
                details=[{"field": field, "issue": "timezone offset required"}],
            )

    rows, next_cursor = await AlertService(session).list_alerts(
        limit=limit,
        cursor=cursor,
        status=incident_status.value if incident_status else None,
        severity=severity.value if severity else None,
        source=source.lower() if source else None,
        from_time=require_aware(from_time) if from_time else None,
        to_time=require_aware(to_time) if to_time else None,
    )
    items = [
        AlertListItem(
            alert_id=str(alert.id),
            source=alert.source,
            event_type=alert.event_type,
            event_time=alert.event_time,
            username=event.username,
            source_ip=event.source_ip,
            host=event.host,
            outcome=event.outcome,
            failure_count=event.failure_count,
            severity=incident.severity,
            risk_score=incident.risk_score,
            status=incident.status,
            confidence=incident.confidence,
            created_at=alert.created_at,
        )
        for alert, event, incident in rows
    ]
    return AlertListResponse(items=items, next_cursor=next_cursor)


@router.get("/{alert_id}", response_model=AlertDetail, summary="Get alert detail")
async def get_alert(alert_id: uuid.UUID, session: SessionDep) -> AlertDetail:
    """Return raw payload, normalised event and linked incident for one alert."""
    alert, _event, incident = await AlertService(session).get_alert(alert_id)
    return AlertDetail(
        alert_id=str(alert.id),
        source=alert.source,
        event_type=alert.event_type,
        event_time=alert.event_time,
        raw_event=alert.raw_event,
        normalized_event=NormalizedEventView.model_validate(
            {**alert.normalized_event, "event_time": alert.event_time}
        ),
        incident=_incident_summary(incident),
        duplicate_of=(
            str(alert.duplicate_of) if alert.duplicate_of is not None else None
        ),
        created_at=alert.created_at,
    )
