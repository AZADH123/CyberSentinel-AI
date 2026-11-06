"""Human review decision endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request, status

from cybersentinel.api.deps import SessionDep
from cybersentinel.api.middleware.correlation import correlation_for_request
from cybersentinel.schemas.review import ReviewCreate, ReviewResponse
from cybersentinel.services.review_service import ReviewService

router = APIRouter(prefix="/incidents", tags=["reviews"])


@router.post(
    "/{incident_id}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a human review for an incident",
)
async def review_incident(
    incident_id: str,
    payload: ReviewCreate,
    request: Request,
    session: SessionDep,
) -> ReviewResponse:
    """Record an analyst/reviewer decision (accept, reject, escalate)."""
    correlation_id = correlation_for_request(request) or "unknown"
    return await ReviewService(session).review_incident(
        incident_id, payload, correlation_id=correlation_id
    )
