"""Investigation lifecycle endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request, status

from cybersentinel.api.deps import SessionDep
from cybersentinel.api.middleware.correlation import correlation_for_request
from cybersentinel.schemas.investigation import (
    InvestigationDetail,
    InvestigationStartResponse,
)
from cybersentinel.services.investigation_service import InvestigationService

router = APIRouter(tags=["investigations"])


@router.post(
    "/alerts/{alert_id}/investigate",
    response_model=InvestigationStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start an investigation for an alert",
)
async def start_investigation(
    alert_id: uuid.UUID,
    request: Request,
    session: SessionDep,
) -> InvestigationStartResponse:
    """Launch an automated triage and analysis investigation for the specified alert."""
    correlation_id = correlation_for_request(request) or "unknown"
    return await InvestigationService(session).start_investigation(
        alert_id, correlation_id=correlation_id
    )


@router.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationDetail,
    summary="Get investigation status and report",
)
async def get_investigation(
    investigation_id: str,
    session: SessionDep,
) -> InvestigationDetail:
    """Poll investigation execution state, node trace, and final report."""
    return await InvestigationService(session).get_investigation(investigation_id)
