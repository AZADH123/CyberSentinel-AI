"""Review decision use cases."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from cybersentinel.core.constants import Disposition, IncidentStatus
from cybersentinel.core.errors import ConflictError, NotFoundError
from cybersentinel.db.models import AuditLog, Review
from cybersentinel.db.repositories.incidents import IncidentRepository
from cybersentinel.schemas.review import ReviewCreate, ReviewResponse
from cybersentinel.utils.time import utc_now

logger = logging.getLogger(__name__)

DISPOSITION_TO_STATUS = {
    Disposition.ACCEPT: IncidentStatus.ACCEPTED,
    Disposition.REJECT: IncidentStatus.REJECTED,
    Disposition.ESCALATE: IncidentStatus.ESCALATED,
}


class ReviewService:
    """Coordinate human review validation and state transitions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.incidents = IncidentRepository(session)

    async def review_incident(
        self,
        incident_id: str,
        payload: ReviewCreate,
        *,
        correlation_id: str,
    ) -> ReviewResponse:
        incident = await self.incidents.get(incident_id)
        if incident is None:
            raise NotFoundError("incident", incident_id)

        # Conflicting second decision returns 409
        if incident.status in {
            IncidentStatus.ACCEPTED.value,
            IncidentStatus.REJECTED.value,
            IncidentStatus.ESCALATED.value,
        }:
            raise ConflictError(
                "invalid_state_transition",
                f"Incident {incident_id} has already been reviewed (status: {incident.status})",
                [{"field": "status", "issue": "already terminal or reviewed"}],
            )

        new_status = DISPOSITION_TO_STATUS[payload.disposition]
        reviewed_at = utc_now()

        review = Review(
            incident_id=incident.id,
            reviewer=payload.reviewer,
            disposition=payload.disposition.value,
            notes=payload.notes,
            reviewed_at=reviewed_at,
        )
        self.session.add(review)

        incident.status = new_status.value
        incident.updated_at = reviewed_at

        self.session.add(
            AuditLog(
                actor=payload.reviewer,
                action=f"incident.reviewed.{payload.disposition.value}",
                entity_type="incident",
                entity_id=incident.id,
                outcome="success",
                correlation_id=correlation_id,
                detail={
                    "disposition": payload.disposition.value,
                    "notes": payload.notes,
                },
            )
        )
        await self.session.flush()

        return ReviewResponse(
            incident_id=incident.id,
            disposition=payload.disposition,
            reviewer=payload.reviewer,
            reviewed_at=reviewed_at,
            incident_status=new_status,
            executed_actions=[],
        )
