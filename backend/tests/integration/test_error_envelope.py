"""Error envelope contract tests (FR-9.1)."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import alert_payload


async def test_error_envelope_shape(client: AsyncClient) -> None:
    response = await client.get("/api/v1/alerts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    envelope = response.json()
    assert set(envelope.keys()) == {"error"}
    error = envelope["error"]
    assert set(error.keys()) == {"code", "message", "details", "correlation_id"}
    assert error["code"] == "not_found"
    assert isinstance(error["details"], list)
    assert error["correlation_id"]


async def test_correlation_id_header_matches_body(client: AsyncClient) -> None:
    response = await client.post("/api/v1/alerts", json=alert_payload(failure_count=-1))
    header = response.headers.get("x-correlation-id")
    assert header
    assert response.json()["error"]["correlation_id"] == header


async def test_validation_error_details_named(client: AsyncClient) -> None:
    response = await client.post("/api/v1/alerts", json=alert_payload(host="bad host!"))
    assert response.status_code == 422
    details = response.json()["error"]["details"]
    assert any(d["field"] == "host" for d in details)
