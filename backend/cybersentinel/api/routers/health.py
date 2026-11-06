"""Readiness and liveness endpoint."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from cybersentinel.api.deps import DatabaseDep, SettingsDep
from cybersentinel.schemas.health import (
    DatabaseCheck,
    EnrichmentCheck,
    HealthChecks,
    HealthResponse,
    LlmCheck,
)

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Liveness and readiness")
async def health(
    settings: SettingsDep,
    database: DatabaseDep,
) -> HealthResponse:
    """Report database, enrichment and LLM readiness separately.

    The HTTP status stays 200 for a reachable process; the body distinguishes ``ok`` from
    ``degraded`` so orchestration can inspect a single contract.
    """
    database_check: DatabaseCheck
    try:
        latency_ms = await asyncio.wait_for(database.ping(), timeout=3.0)
        database_check = DatabaseCheck(status="ok", latency_ms=latency_ms)
    except TimeoutError:
        database_check = DatabaseCheck(status="error", detail="database check timed out")
    except Exception:
        database_check = DatabaseCheck(status="error", detail="database unreachable")

    enrichment_configured = settings.enrichment_mode != "live" or settings.virustotal_configured
    llm_configured = not settings.llm_enabled or settings.gemini_configured
    overall = "ok" if database_check.status == "ok" else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        checks=HealthChecks(
            database=database_check,
            enrichment=EnrichmentCheck(
                mode=settings.enrichment_mode, configured=enrichment_configured
            ),
            llm=LlmCheck(enabled=settings.llm_enabled, configured=llm_configured),
        ),
    )
