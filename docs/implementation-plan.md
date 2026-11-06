# Implementation Plan and Checklist (M1–M6)

## Delivery rules

- The PRD is the contract. Milestones are sequential; a gate is evidenced with commands, not
  asserted.
- Work is kept runnable at every gate. No placeholder modules, no fake "completed" rows.
- After each milestone: tests, lint, typing, import-boundary check, migration check, structure
  review, traceability update, then report completed/incomplete requirements and wait for
  approval before the next milestone.
- No Redis/Kafka/Celery/Kubernetes. No containment or remediation capability.

## Dependency graph

```text
M1 schema/config/API ─► M2 domain/evidence/enrichment ─► M3 graph ─► M4 report/review ─► M5 UI ─► M6 packaging/eval
                                      │                                  ▲
                                      └──── deterministic fixtures ──────┘
```

Critical path: alert schema → risk/rules → graph state → report validator → UI. Enrichment,
ATT&CK catalogue and UI can absorb schedule slippage because each has a deterministic path.

---

## M1 — Foundations and alert round trip

### Scope

| Area | Deliverable |
| --- | --- |
| Repository | backend/frontend/docs/deploy structure, `.gitignore`, `.env.example`, Makefile |
| Python | `pyproject.toml`, pinned `requirements.txt`, Ruff, mypy, pytest config, venv instructions |
| Config | Pydantic Settings for every variable in the master brief |
| Logging | JSON logs, request/correlation context, secret-filtering formatter |
| Database | async SQLAlchemy foundation, `alerts`, `events`, `incidents`, `audit_logs`, indexes/FKs |
| Migrations | Alembic async environment + initial revision; no runtime `create_all()` |
| Validation | full §9.1 alert contract: timezone, count, IP, host, raw-event limits, enums |
| API | app factory, correlation ID, body limit, rate limit, error envelope, `/health`, POST/GET alerts |
| Service | transactional create, idempotency replay, near-duplicate link, incident creation, audit |
| Tests | ≥ 12: happy path, 422 cases, envelope, idempotency, duplicate, 413, health, migration |
| Docs | traceability, architecture, ERD, flows, API, ADRs, open questions, README seed |

### Acceptance commands

```powershell
cd backend
..\ .venv\Scripts\Activate.ps1
alembic upgrade head
pytest -q
ruff check cybersentinel tests
mypy cybersentinel
```

### Gate G1 checklist

- [ ] valid alert returns 201 with alert/incident IDs and is retrievable
- [ ] raw payload + normalized event persisted
- [ ] naive timestamp → 422 with `event_time` detail
- [ ] negative and >10 000 failure counts → 422
- [ ] invalid IP/hostname in `source_ip` → 422
- [ ] same idempotency key returns 200 and one row
- [ ] near duplicate links original and does not create a second incident
- [ ] all errors use the envelope with `correlation_id`
- [ ] 300 KB body → 413
- [ ] `/health` reports database readiness
- [ ] `alembic upgrade head` succeeds on an empty database
- [ ] ≥ 8 tests green (target 15)
- [ ] `domain/` is I/O-free (initial layering test)

---

## M2 — Evidence substrate, rules, scoring and enrichment

### Scope

- 24 deterministic events, 4 users, 3 hosts, 6 addresses; idempotent seeder.
- `domain/correlation.py`: ±window, user/IP/host reasons, chronological, cap 200, anchor.
- `domain/rules.py`: R-01…R-06 exact thresholds and points; absence yields gaps not points.
- `domain/risk_engine.py`: additive cap 100, bands, confidence, `risk-v1.json`; worked examples
  A=29 low, B=64 medium, C=84 high.
- Evidence service: append-only, `EV-NNN`, canonical checksum, supersedes, tamper detection.
- `domain/ip_policy.py`: every row of §9.3.1 incl. IPv6; reason codes.
- VirusTotal adapter: mock default, live opt-in, cache TTL, timeout, 2 retries/backoff, budget,
  `provider_status`, fixtures for malicious/suspicious/clean/timeout/429.
- Incident/evidence read APIs, incident queue ordering.
- Tests: rule boundaries, band edges 24/25/49/50/74/75, IP rows, correlation window/cap,
  cache/budget/timeout, seeder idempotency, evidence checksum.

### Gate G2

- [ ] Scenario A returns 29/low with visible arithmetic
- [ ] seeded timeline chronological with match reasons and anchor
- [ ] all IP-policy rows tested
- [ ] timeout yields `provider_status=timeout`, no exception
- [ ] cache hit performs zero HTTP calls
- [ ] evidence checksum tamper is detected

---

## M3 — LangGraph, runner and degradation

### Scope

- `InvestigationState` TypedDict + Pydantic node outputs; `operator.add` error/trace reducers.
- Nodes: triage, correlate, enrich, attack_map, risk, report, validate, repair, fallback,
  degrade; topology per §7.5.2.
- Deterministic fast path; checkpoints (`SqliteSaver` local / `PostgresSaver` Compose).
- Per-node timeout/retry policy; typed error records; `degrade` terminal output.
- Runner: `asyncio` registry, `Semaphore(2)`, one active run per alert, cancellation flag.
- Startup recovery: stale `running` → `interrupted`; resume path never fabricates completion.
- `POST /investigate` 202, `GET /investigations/{id}` polling with completed/current nodes.
- Tests: happy path, fast path, fault injection, timeout, duplicate start 409, progress
  ordering, restart recovery, concurrent limit.

### Gate G3

- [ ] `LLM_ENABLED=false` produces a schema-valid report for Scenario C
- [ ] score 84/high, ≥ 2 ATT&CK candidates, 100% evidence resolution
- [ ] injected triage failure → `failed` with minimal factual output and no stack leak
- [ ] stale run marked `interrupted`, not completed

---

## M4 — Reports, ATT&CK, Gemini and review

### Scope

- Curated, versioned ATT&CK subset (T1110, T1110.003, T1078, T1078.004, T1133, T1098, T1021,
  T1021.001); 7 behaviour rules; ≤ 5 candidates; evidence + rationale; canonical URLs.
- Report Pydantic/JSON Schema: observations, hypotheses + alternatives, gaps, non-destructive
  actions, timeline, generation metadata, `human_approval_required`.
- Gemini adapter: schema-constrained, one call + ≤1 repair, timeout, kill switch, redacted
  context, fenced untrusted text, no tools.
- Deterministic template fallback + degradation notes.
- Validator: schema, evidence IDs + checksums, technique allowlist, band/severity consistency,
  approval flag, `destructive=false`; immutable report persistence.
- Review API + audit; conflicting decision 409; `executed_actions=[]`.
- Tests: schema, unknown evidence, tampered checksum, unknown technique, severity mismatch,
  LLM outage, invalid JSON twice, prompt injection score/mapping equality, review flow.

### Gate G4

- [ ] LLM-on narrative passes the same validator
- [ ] two forced schema failures yield a valid degraded template
- [ ] review persists reviewer/notes/timestamp and triggers no network call
- [ ] unknown evidence/technique rejected
- [ ] prompt injection changes neither score nor mappings

---

## M5 — React dashboard

### Scope

- React 18 + Vite + TypeScript + TanStack Query + Tailwind; typed API client from contracts.
- Screens: alert queue, incident detail (summary, timeline, score breakdown, ATT&CK, gaps,
  degradation, report), review form; optional benchmark screen.
- 1 s polling while investigating; no optimistic review; copyable `INV-…:EV-001` chips.
- Explicit live/mock/skipped/timeout/degraded/failed states with text badges, keyboard access,
  contrast ≥ 4.5:1.
- Playwright smoke tests for the three screens and mock/degraded badges.
- Frontend served by Vite locally; production build handled in M6.

### Gate G5

- [ ] browser-only flow: alert → investigate → progress → report → evidence → review
- [ ] all fault states reachable through demo fixtures
- [ ] ≥ 40 tests overall; ≥ 80% lines on `domain/` and `services/`
- [ ] no `dangerouslySetInnerHTML`; XSS fixture rendered as text

---

## M6 — Packaging, evaluation and release

### Scope

- Multi-stage backend/frontend Dockerfiles; nginx config + API proxy.
- Compose with `db`, `api`, `web`; health checks; migrations + idempotent seed before serve;
  `127.0.0.1` published ports; no public DB; persistent `pgdata`; `.env` from root.
- PostgreSQL 16 migration verification; SQLite test path retained.
- Security suite S-01…S-10, layering, no-execution, limits, secret scan.
- Evaluation harness: 24 scenarios × 3 repetitions, warm-up discard, manual/assisted timing
  schema, CSV/Markdown output, honest "not supported" path.
- README, Windows/Docker/troubleshooting docs, evaluation report, quickstart verification,
  architecture diagrams synchronised with code.
- Fresh-clone test by a person who has not seen the project.

### Gate G6

- [ ] `docker compose up` reaches the demo from a clean clone
- [ ] ≥ 24 scenarios pass; evidence resolution 100%
- [ ] coverage target evidenced
- [ ] no secrets/real indicators in tree or history
- [ ] measured evaluation table with sample size and limitations
- [ ] 3–5 minute demo path documented

---

## Cut lines (in order, only if needed)

1. Live VirusTotal off; mock-only with explicit labels.
2. Drop benchmark UI; keep CLI table.
3. Drop SSE (already out of v1); keep polling.
4. Drop LLM narrative; deterministic template becomes primary.
5. Drop `account_change`; authentication only.

Never cut: evidence validation, degradation matrix, review gate, mock/degraded disclosure.

## Immediate next step

Implement M1 only. Before M2, publish the gate report and wait for approval.
