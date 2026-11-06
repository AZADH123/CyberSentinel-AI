# API Reference

Base path: `/api/v1` for resources, `/health` unversioned.
Media type: `application/json; charset=utf-8`. All timestamps are RFC 3339 UTC with `Z`.
Authentication: none in v1 (localhost only); reviewer identity comes from the review payload
or configured `REVIEWER_NAME`.

## Conventions

| Concern | Behaviour |
| --- | --- |
| Correlation | Every response has `X-Correlation-Id`; errors repeat it in the body |
| Idempotency | `Idempotency-Key` header wins over body key for alert creation |
| Pagination | `?limit=50&cursor=<opaque>` → `{"items": [...], "next_cursor": null}` |
| Rate limit | 60 req/min/client; `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| Errors | `{"error": {code, message, details, correlation_id}}` |
| IDs | Opaque strings; clients must not parse them |
| Reviewer | `REVIEWER_NAME` default; request body `reviewer` overrides in v1 |

## Endpoint index

| Method | Path | Success | Milestone |
| --- | --- | --- | --- |
| GET | `/health` | 200 | M1 |
| POST | `/api/v1/alerts` | 201 / 200 replay | M1 |
| GET | `/api/v1/alerts` | 200 | M1 |
| GET | `/api/v1/alerts/{alert_id}` | 200 | M1 |
| POST | `/api/v1/alerts/{alert_id}/investigate` | 202 | M3 |
| GET | `/api/v1/investigations/{investigation_id}` | 200 | M3 |
| POST | `/api/v1/investigations/{investigation_id}/cancel` | 202 | M3 (P1) |
| GET | `/api/v1/incidents` | 200 | M2 |
| GET | `/api/v1/incidents/{incident_id}` | 200 | M2 |
| GET | `/api/v1/incidents/{incident_id}/evidence` | 200 | M2 |
| POST | `/api/v1/incidents/{incident_id}/review` | 201 | M4 |

## GET /health

```json
{
  "status": "ok",
  "version": "0.1.0",
  "checks": {
    "database": {"status": "ok", "latency_ms": 2},
    "enrichment": {"mode": "mock", "configured": true},
    "llm": {"enabled": false, "configured": false}
  }
}
```

`status` is `degraded` when a non-critical dependency is unconfigured/unavailable. Database
failure returns HTTP 503 with the standard error envelope for readiness probes.

## POST /api/v1/alerts

### Request

```http
POST /api/v1/alerts
Content-Type: application/json
Idempotency-Key: demo-0001
```

```json
{
  "source": "lab-auth-simulator",
  "event_type": "authentication",
  "event_time": "2026-11-03T02:30:00Z",
  "username": "admin",
  "source_ip": "198.51.100.24",
  "host": "vpn-01",
  "outcome": "failure",
  "failure_count": 18,
  "asset_criticality": "high",
  "raw_event": {"message": "Repeated login failures"}
}
```

### Validation rules

| Field | Rule |
| --- | --- |
| `source` | 1–64 chars, `^[a-z0-9][a-z0-9._-]*$`, lowercased |
| `event_type` | `authentication`, `authorization`, `account_change` |
| `event_time` | RFC 3339 **with offset**; ≤ now + 5 min; ≥ now − 90 days; UTC seconds |
| `username` | 1–128 chars, no control chars, trimmed |
| `source_ip` | IPv4/IPv6 literal, canonicalised |
| `host` | 1–253 chars, `^[A-Za-z0-9][A-Za-z0-9.-]*$`, lowercased |
| `outcome` | `success`, `failure`, `unknown` |
| `failure_count` | integer 0…10 000, default 0 |
| `asset_criticality` | `low`, `medium`, `high`, `critical`, default `medium` + gap |
| `raw_event` | object, ≤ 16 KiB serialised, keys ≤ 64 chars, depth ≤ 5, never executed |
| `idempotency_key` | 8–128 chars; header takes precedence |

### Responses

`201 Created` for a new alert:

```json
{
  "alert_id": "0192456e-6f47-7c31-9a1e-2f0c8d3b7a55",
  "incident_id": "INC-2026-0001",
  "status": "open",
  "event_time": "2026-11-03T02:30:00Z",
  "created_at": "2026-11-03T02:35:10Z",
  "duplicate_of": null
}
```

`200 OK` for an identical replay with the same idempotency key; returns the original IDs.
A near-duplicate without a key returns 201 with `duplicate_of` set and the original incident.

### Errors

| Status | Code | Cause |
| --- | --- | --- |
| 400 | `malformed_request` | invalid JSON / content type |
| 409 | `idempotency_key_conflict` | same key, different content |
| 413 | `payload_too_large` | body > 256 KiB |
| 422 | `validation_error` | schema/field violation |
| 422 | `unsupported_event_type` | event type outside v1 |
| 429 | `rate_limited` | throttle exceeded |

## GET /api/v1/alerts

Query: `limit` (1–100, default 50), `cursor`, `status`, `severity`, `source`, `from`, `to`.
Returns alerts newest-first with linked incident summary.

## GET /api/v1/alerts/{alert_id}

Returns raw and normalised events, linked incident, duplicate lineage and the current
investigation summary. Unknown ID → `404 not_found`.

## POST /api/v1/alerts/{alert_id}/investigate

Start one investigation. Response `202`:

```json
{
  "investigation_id": "INV-9F2A41C8",
  "status": "running",
  "started_at": "2026-11-03T02:36:02Z",
  "poll": "/api/v1/investigations/INV-9F2A41C8"
}
```

Active run for the same alert → `409 investigation_in_progress`.

## GET /api/v1/investigations/{investigation_id}

```json
{
  "investigation_id": "INV-9F2A41C8",
  "status": "running",
  "progress": {
    "completed_nodes": ["triage", "correlate", "enrich"],
    "current_node": "attack_map",
    "elapsed_ms": 2140
  },
  "trace": [
    {"node": "triage", "outcome": "ok", "duration_ms": 12},
    {"node": "enrich", "outcome": "degraded", "duration_ms": 5003,
     "detail": "provider timeout, 2 attempts"}
  ]
}
```

Terminal statuses: `completed`, `completed_degraded`, `failed`, `cancelled`, `interrupted`.
When present, `report` is the immutable latest report version.

## GET /api/v1/incidents

Queue sorted by risk score desc then created_at desc. Filters: `status`, `severity`, `limit`,
`cursor`. Response includes score, band, confidence, status and review state.

## GET /api/v1/incidents/{incident_id}

Returns incident, latest report, evidence timeline, ATT&CK candidates, enrichment states,
missing information, degradation notes and review history.

## GET /api/v1/incidents/{incident_id}/evidence

Returns evidence rows with `id`, qualified ID, kind, source, reference, captured_at, value and
checksum. Query `kind` optionally filters. Evidence is append-only.

## POST /api/v1/incidents/{incident_id}/review

```json
{
  "reviewer": "mentor",
  "disposition": "escalate",
  "notes": "Confirm with the account owner; group change unexplained."
}
```

`201 Created`:

```json
{
  "incident_id": "INC-2026-0001",
  "disposition": "escalate",
  "reviewer": "mentor",
  "reviewed_at": "2026-11-03T09:12:00Z",
  "incident_status": "escalated",
  "executed_actions": []
}
```

- `notes` required (non-blank) for `reject` and `escalate`.
- Conflicting second decision → `409 invalid_state_transition`.
- Review performs no network calls and changes no external state. `executed_actions` is always
  `[]` by contract.

## Error codes

| HTTP | Code | When |
| --- | --- | --- |
| 400 | `malformed_request` | unparseable JSON / wrong content type |
| 404 | `not_found` | unknown alert, investigation or incident |
| 409 | `investigation_in_progress` | second active start |
| 409 | `invalid_state_transition` | conflicting review / wrong incident state |
| 413 | `payload_too_large` | body > 256 KiB |
| 422 | `validation_error` | field-level failure |
| 422 | `unsupported_event_type` | event type outside v1 |
| 429 | `rate_limited` | throttle |
| 500 | `internal_error` | unhandled; internals never leaked |
| 503 | `dependency_unavailable` | database unreachable |
| 504 | `investigation_timeout` | wall-clock budget exceeded |

## Interactive documentation

FastAPI exposes OpenAPI at `/openapi.json` and Swagger UI at `/docs` on the API port. The
checked-in contract tests treat OpenAPI and runtime behaviour as one contract.
