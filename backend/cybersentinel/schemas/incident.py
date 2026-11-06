"""Incident API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cybersentinel.core.constants import Confidence, IncidentStatus, Severity


class IncidentSummary(BaseModel):
    """Compact incident projection embedded in alert responses."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    status: IncidentStatus
    severity: Severity
    risk_score: int = Field(ge=0, le=100)
    risk_band: Severity
    confidence: Confidence
    created_at: datetime


class IncidentListResponse(BaseModel):
    """Cursor-paginated incident queue."""

    items: list[IncidentSummary]
    next_cursor: str | None = None


class EvidenceItem(BaseModel):
    """Single evidence row projection."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    investigation_id: str
    evidence_key: str
    kind: str
    source: str
    reference: str
    captured_at: datetime
    value: dict[str, Any]
    checksum: str
    supersedes: str | None = None


class IncidentDetail(BaseModel):
    """Full incident view for the analyst UI."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    alert_id: str
    status: IncidentStatus
    severity: Severity
    risk_score: int = Field(ge=0, le=100)
    risk_band: Severity
    confidence: Confidence
    created_at: datetime
    updated_at: datetime
    alert_summary: dict[str, Any] | None = None
    latest_investigation_id: str | None = None
    investigation_status: str | None = None
    report: dict[str, Any] | None = None
    reviews: list[dict[str, Any]] = Field(default_factory=list)
