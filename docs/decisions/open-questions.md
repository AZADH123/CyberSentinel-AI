# Open Questions and Resolved Ambiguities

The PRD is the source of truth. Where it is silent or internally inconsistent, the safest
interpretation is recorded here and implemented behind a tested interface. Questions from PRD
§18 are preserved with their IDs.

## PRD open questions

| ID | Question | Current treatment | Impact if changed |
| --- | --- | --- | --- |
| Q-01 | Is live VirusTotal available on evaluation day? | Mock is the default and the documented evaluation mode. Live is opt-in. | Only what enrichment claims can be made; labels stay honest either way. |
| Q-02 | Can a second reviewer score ≥ 5 reports? | Evaluation protocol supports one reviewer, reports the limitation. | Inter-rater agreement cannot be claimed without a second reviewer. |
| Q-03 | Does manual baseline include reading seeded evidence or realistic pivoting? | Declare "same seeded evidence sources" before timing; do not compare different tasks. | Changes measured time difference materially. |
| Q-04 | Is `account_change` in v1? | **Included**, because SC-06 and R-04 depend on it. Authentication is the primary API path; account-change events support correlation. | Removing it drops R-04 and the 84-point reference case. |
| Q-05 | Is 30 minutes defensible, or per-scenario configurable? | Global `CORRELATION_WINDOW_MINUTES=30`; scenarios may override through test settings, while production config remains global. | Window width changes timeline and R-06 evidence. |
| Q-06 | Documented LLM fallback if Gemini is unavailable? | Deterministic template is the fallback; no second LLM provider is added. | Adding a provider is a scope increase and another failure surface. |

## Implementation ambiguities

### OQ-01 — Where is an immutable report stored?

PRD §8.2 has no `reports` table, but §9.6 requires immutable, versioned reports. **Resolution:**
add an append-only `reports` table (ADR-012). The listed tables are treated as a minimum.

### OQ-02 — Missing `failure_count` on a failure outcome

§9.1.2 says default `0` when omitted; SC-10 says "treated as 1, gap listed". These conflict.
**Resolution for M1:** follow the explicit field contract (default 0) and record a validation
gap only when the caller omitted the field. Revisit at M2 against SC-10 acceptance; any change
requires a PRD version bump because it affects scores.

### OQ-03 — What exactly is `alerts.raw_event`?

FR-1.2 says persist the raw payload; §9.1.2 defines a nested `raw_event` object. **Resolution:**
store the complete validated request object in `alerts.raw_event` (including the nested
`raw_event` field), and store the canonical normalised event in `alerts.normalized_event`.
This satisfies "raw payload" without discarding the nested message. Tests assert the nested
message survives.

### OQ-04 — `reviews` idempotency

§10.1 says idempotency is honoured on review, but the review contract has no key field and
`reviews` has no key column. **Resolution:** defer review idempotency to M4; the safest M4
implementation is an `Idempotency-Key` header and a unique `(incident_id, idempotency_key)`
column added by migration. Until then, conflicting dispositions return 409 and duplicate
identical dispositions return the existing review with 200.

### OQ-05 — Near-duplicate alerts and incident linkage

SC-18 requires `duplicate_of` and "incident not duplicated", while every alert normally has
one incident. **Resolution:** create a new alert row with `duplicate_of`, do not create a
second incident, and return the original incident ID in the create response. The duplicate
alert is visible for audit but is not a second unit of work.

### OQ-06 — Evidence `supersedes` is named but not in the table definition

§8.4 permits corrections via `supersedes`, but §8.2's `evidence` fields omit it. **Resolution:**
add nullable self-FK `supersedes`; updates/deletes remain forbidden.

### OQ-07 — "PostgreSQL 16 primary" vs "SQLite default" for M1

**Resolution:** M1 local default is SQLite for a zero-dependency round trip; Compose and the
production profile use PostgreSQL 16. No dialect-specific JSONB operators leak into services.
See ADR-013.

### OQ-08 — Invalid technique wording ("is"/"confirmed") vs legitimate phrases

FR-5.4 forbids confirmed attribution, but a blanket ban on "is" also forbids grammatically
necessary text. **Resolution:** use a narrow wording validator that rejects attribution
phrases (`confirmed`, `attributable to`, `the attacker is`, `is definitely`) while allowing
descriptive "is consistent with". The catalogue never names an actor.

### OQ-09 — Live-mode keys at startup

The PRD says missing keys should be visible and startup should refuse default keys, but does
not define placeholder patterns. **Resolution:** `.env.example` ships empty; live/LLM-enabled
mode fails closed on empty, `changeme`, `replace-me`, `demo`, or keys shorter than 16 chars.
Mock mode starts with no keys.

### OQ-10 — Report action "priority" vocabulary

§9.6 shows `immediate` and `next` but does not define an enum. **Resolution:** fixed enum
`immediate | next | monitor`; all actions require `destructive: false`. No operational action
is exposed as executable.

## Change control

Any resolution that changes a P0 contract, risk weight, severity boundary or report field
requires a PRD version bump and reviewer sign-off. Until then, this file is the audit trail
for implementation choices.
