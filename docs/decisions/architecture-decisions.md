# Architecture Decision Record

The PRD's ADR-001…ADR-011 are accepted as baseline. This file restates them for local
traceability and records ADRs added during implementation. A new ADR is required for any
change that alters a P0 contract, the risk weights, report schema or safety boundary.

## Baseline decisions

| ID | Decision | Consequence |
| --- | --- | --- |
| ADR-001 | One LangGraph graph with specialist nodes, not a multi-agent supervisor | Debubggable, cheap, serialisable state; multi-agent deferred |
| ADR-002 | Deterministic scoring and ATT&CK selection; LLM writes prose only | Every score/mapping is regression-testable and auditable |
| ADR-003 | `202` + polling with an in-process runner | No Redis/Celery; concurrency limit 2; queue is a v2 upgrade |
| ADR-004 | SQLAlchemy abstraction over SQLite/PostgreSQL | M1 is not blocked on infrastructure; Compose runs PostgreSQL |
| ADR-005 | Read-only tool boundary | No block/disable/isolate/execute capability exists |
| ADR-006 | Mock-first enrichment with labelled fixtures | Offline, deterministic demo; live/mock never conflated |
| ADR-007 | Evidence as an append-only, checksummed table | Report is a view; citations survive report regeneration |
| ADR-008 | Additive, capped, versioned risk weights | One-line explainability; no false probability claim |
| ADR-009 | No auth/RBAC; localhost binding | Honest prototype boundary; disclosed limitation |
| ADR-010 | Evidence IDs scoped per investigation | Short quotable IDs; qualified form across scopes |
| ADR-011 | Pydantic models are the single schema source | API, validator and exported JSON Schema cannot drift |

## Implementation decisions

### ADR-012 — Persist reports in a dedicated append-only `reports` table

**Context.** PRD §9.6 requires immutable reports with corrections as new versions, but §8.2
does not list a `reports` table and the master table list omits one. Storing reports only in
`investigations.graph_state` would make them mutable and mix execution state with output.

**Decision.** Add `reports` with `(investigation_id, version)` unique, JSON content, schema
version, degraded flag and generation metadata. Inserts only; a correction is version + 1.

**Consequences.** One extra table and join, but report immutability and audit are real rather
than conventional. The PRD table inventory is treated as a minimum, not a closed set.

### ADR-013 — PostgreSQL 16 is the deployment database; SQLite is test/fallback only

**Context.** The PRD says PostgreSQL 16 as primary in the master brief and §7.3, while §7.8
and ADR-004 permit SQLite for Day 1 and tests.

**Decision.** Docker Compose and the published `.env.example` use PostgreSQL 16 with JSONB.
SQLite (`sqlite+aiosqlite`) is supported for isolated tests and local M1 convenience. The type
layer uses portable UUID/JSON variants; repositories avoid dialect-specific SQL except
explicitly tested capabilities.

**Consequences.** Both paths are tested. PostgreSQL-only features (partial indexes, JSONB
operators) must be guarded or kept out of shared code.

### ADR-014 — Async SQLAlchemy end-to-end

**Context.** FastAPI and HTTPX are async; graph nodes perform DB reads/writes.

**Decision.** Use SQLAlchemy 2.0 async engine/session with `asyncpg` in production and
`aiosqlite` in tests. Alembic uses the async migration environment.

**Consequences.** No blocking DB calls in the event loop. Test fixtures must dispose engines
and avoid cross-event-loop session reuse.

### ADR-015 — Preserve machine-readable field paths in validation errors

**Context.** The PRD's error envelope uses `details: [{field, issue}]`, while Pydantic returns
nested `loc` tuples.

**Decision.** The validation handler serialises `loc` as a dotted path (excluding `body`) and
uses `msg` as the issue. Error codes remain stable; messages are reviewer-readable.

**Consequences.** Field names are stable for UI inline errors and tests; adding a nested
model does not require a new envelope shape.

### ADR-016 — Correlation ID is server-generated ULID

**Context.** The PRD requires a correlation ID per request and a ULID example, but does not
say whether clients may supply one.

**Decision.** Always generate a new 26-character Crockford ULID server-side. Do not trust a
client-supplied correlation ID. Return it in `X-Correlation-Id` and the error envelope.

**Consequences.** No log-injection or ID-spoofing path; clients cannot correlate retries by
providing their own ID.

### ADR-017 — Idempotency-key reuse with different content returns 409

**Context.** FR-1.6 specifies identical replays; behaviour for key reuse with changed content
is unspecified.

**Decision.** Store a canonical request fingerprint alongside the key. Identical fingerprint →
200 with original IDs; different fingerprint → `409 idempotency_key_conflict`.

**Consequences.** Prevents a client from accidentally receiving a record for different input.
The new code is documented in the API reference and tested.

### ADR-018 — M1 seeds and tests use deterministic synthetic identifiers

**Context.** Reproducibility requires stable data, but UUIDv7 alerts are time-based.

**Decision.** Seed records use fixed UUIDs and natural keys, and the seeder checks existence
before insert. Tests never depend on wall-clock IDs; they capture returned IDs.

**Consequences.** Re-running the seed is a no-op. Production-created alerts remain UUIDv7.
