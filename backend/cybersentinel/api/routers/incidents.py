"""Incident read endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from cybersentinel.api.deps import SessionDep
from cybersentinel.core.constants import IncidentStatus, Severity
from cybersentinel.schemas.incident import (
    EvidenceItem,
    IncidentDetail,
    IncidentListResponse,
)
from cybersentinel.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=IncidentListResponse, summary="List incidents")
async def list_incidents(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
    status: IncidentStatus | None = None,
    severity: Severity | None = None,
) -> IncidentListResponse:
    """Return incidents ordered by risk score descending then created_at descending."""
    items, next_cursor = await IncidentService(session).list_incidents(
        limit=limit,
        cursor=cursor,
        status=status.value if status else None,
        severity=severity.value if severity else None,
    )
    return IncidentListResponse(items=items, next_cursor=next_cursor)


@router.get("/{incident_id}", response_model=IncidentDetail, summary="Get incident detail")
async def get_incident(incident_id: str, session: SessionDep) -> IncidentDetail:
    """Return full incident record including latest report, investigation status, and reviews."""
    return await IncidentService(session).get_incident(incident_id)


@router.get(
    "/{incident_id}/evidence",
    response_model=list[EvidenceItem],
    summary="Get incident evidence",
)
async def get_incident_evidence(
    incident_id: str,
    session: SessionDep,
    kind: str | None = None,
) -> list[EvidenceItem]:
    """Return immutable evidence rows captured for this incident."""
    return await IncidentService(session).get_evidence(incident_id, kind=kind)
