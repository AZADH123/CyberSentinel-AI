"""Investigation API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cybersentinel.core.constants import InvestigationStatus


class InvestigationStartResponse(BaseModel):
    """202 response for POST /alerts/{alert_id}/investigate."""

    investigation_id: str
    status: InvestigationStatus
    started_at: datetime
    poll: str


class InvestigationProgress(BaseModel):
    """Progress snapshot for polling."""

    completed_nodes: list[str] = Field(default_factory=list)
    current_node: str | None = None
    elapsed_ms: int = 0


class InvestigationTraceItem(BaseModel):
    """One node execution record."""

    node: str
    outcome: str
    duration_ms: int
    detail: str | None = None


class InvestigationDetail(BaseModel):
    """Full investigation state returned by GET /investigations/{id}."""

    model_config = ConfigDict(from_attributes=True)

    investigation_id: str
    status: InvestigationStatus
    progress: InvestigationProgress
    trace: list[InvestigationTraceItem] = Field(default_factory=list)
    report: dict[str, Any] | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_summary: str | None = None
