"""Health endpoint contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DatabaseCheck(BaseModel):
    """Database readiness detail without a DSN or credentials."""

    status: Literal["ok", "error"]
    latency_ms: float | None = Field(default=None, ge=0)
    detail: str | None = None


class EnrichmentCheck(BaseModel):
    """Configured enrichment mode and credential presence."""

    mode: Literal["live", "mock", "off"]
    configured: bool


class LlmCheck(BaseModel):
    """Whether optional narrative generation is enabled and configured."""

    enabled: bool
    configured: bool


class HealthChecks(BaseModel):
    """Independent readiness checks."""

    database: DatabaseCheck
    enrichment: EnrichmentCheck
    llm: LlmCheck


class HealthResponse(BaseModel):
    """Liveness and readiness response.

    HTTP is always 200 for a reachable process; the body distinguishes ``ok`` from
    ``degraded`` so a dependency outage does not make the API appear dead.
    """

    status: Literal["ok", "degraded"]
    version: str
    checks: HealthChecks
