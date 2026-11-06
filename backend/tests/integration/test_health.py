"""Health endpoint integration tests (FR-9.2)."""

from __future__ import annotations

from httpx import AsyncClient


async def test_health_reports_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["checks"]["database"]["status"] == "ok"
    assert body["checks"]["database"]["latency_ms"] >= 0
    assert body["checks"]["enrichment"]["mode"] == "mock"
    assert body["checks"]["llm"]["enabled"] is False
    assert "change-me" not in response.text
