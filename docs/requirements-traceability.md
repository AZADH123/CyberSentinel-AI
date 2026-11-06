# Requirements Traceability Matrix

Source of truth: `CyberSentinel_AI_PRD_v2.0.md` (v2.0, 03 November 2026).
Status values are intentionally conservative: a requirement is **Verified** only after its
automated test passes in this repository. `M1` means the requirement is scheduled for the
foundations milestone, not that it is already complete.

> Update rule: change a status only in the same commit that adds or changes the cited test.

## Functional requirements

| Requirement | Milestone | Primary automated test(s) | Status |
| --- | --- | --- | --- |
| FR-1.1 JSON alert ingest / 201 | M1 | `tests/integration/test_alerts_api.py::test_fr_1_1_create_alert_round_trip` | Planned |
| FR-1.2 raw + normalised persistence | M1 | `test_alerts_api.py::test_fr_1_2_raw_and_normalized_persisted` | Planned |
| FR-1.3 timezone-aware timestamps | M1 | `test_alerts_api.py::test_fr_1_3_naive_timestamp_rejected` | Planned |
| FR-1.4 count bounds | M1 | `test_alerts_api.py::test_fr_1_4_failure_count_bounds` | Planned |
| FR-1.5 IP literal validation | M1 | `test_alerts_api.py::test_fr_1_5_invalid_ip_rejected` | Planned |
| FR-1.6 Idempotency-Key | M1 | `test_alerts_api.py::test_fr_1_6_idempotency_key_returns_original` | Planned |
| FR-1.7 near-duplicate flag | M1 | `test_alerts_api.py::test_fr_1_7_near_duplicate_links_original` | Planned |
| FR-2.1 deterministic triage | M2 | `tests/unit/test_triage_rules.py` | Planned |
| FR-2.2 named findings | M2 | `test_triage_rules.py::test_fr_2_2_findings_have_required_fields` | Planned |
| FR-2.3 observed vs inferred | M2 | `test_triage_rules.py::test_fr_2_3_claim_types` | Planned |
| FR-2.4 absence is not evidence | M2 | `test_triage_rules.py::test_fr_2_4_missing_mfa_is_gap_only` | Planned |
| FR-3.1 correlation window | M2 | `tests/unit/test_correlation.py` | Planned |
| FR-3.2 match reasons | M2 | `test_correlation.py::test_fr_3_2_match_reasons` | Planned |
| FR-3.3 bounded read-only correlation | M2 | `test_correlation.py::test_fr_3_3_cap_and_no_writes` | Planned |
| FR-3.4 chronological anchor timeline | M2 | `test_correlation.py::test_fr_3_4_order_and_anchor` | Planned |
| FR-4.1 IP eligibility | M2 | `tests/unit/test_enrichment_policy.py` | Planned |
| FR-4.2 skip reasons surfaced | M2 | `test_enrichment_policy.py::test_fr_4_2_skip_reason_in_gaps` | Planned |
| FR-4.3 indicator cache TTL | M2 | `tests/integration/test_virustotal_adapter.py` | Planned |
| FR-4.4 timeout/retry/budget | M2 | `test_virustotal_adapter.py::test_timeout_retry_budget` | Planned |
| FR-4.5 labelled mock mode | M2 | `test_virustotal_adapter.py::test_mock_result_is_labelled` | Planned |
| FR-4.6 provider failure continuation | M2 | `tests/scenarios/test_degradation_matrix.py` | Planned |
| FR-5.1 curated ATT&CK catalogue | M4 | `tests/unit/test_attack_mapping.py` | Planned |
| FR-5.2 mapping evidence + rationale | M4 | `test_attack_mapping.py::test_fr_5_2_evidence_required` | Planned |
| FR-5.3 canonical technique links | M4 | `test_attack_mapping.py::test_fr_5_3_urls_built_from_id` | Planned |
| FR-5.4 candidate-only wording | M4 | `tests/security/test_attack_catalog_guard.py` | Planned |
| FR-6.1 deterministic 0–100 score | M2 | `tests/unit/test_risk_scoring.py` | Planned |
| FR-6.2 breakdown + ruleset version | M2 | `test_risk_scoring.py::test_fr_6_2_breakdown` | Planned |
| FR-6.3 severity bands | M2 | `test_risk_scoring.py::test_fr_6_3_band_boundaries` | Planned |
| FR-6.4 confidence degradation | M2 | `test_risk_scoring.py::test_fr_6_4_confidence` | Planned |
| FR-7.1 report JSON schema | M4 | `tests/unit/test_report_contract.py` | Planned |
| FR-7.2 evidence resolution | M4 | `tests/security/test_evidence_integrity.py` | Planned |
| FR-7.3 gaps + recommended actions | M4 | `test_report_contract.py::test_fr_7_3` | Planned |
| FR-7.4 human approval flag | M4 | `test_report_contract.py::test_fr_7_4` | Planned |
| FR-7.5 deterministic fallback | M4 | `test_degradation_matrix.py::test_llm_outage` | Planned |
| FR-7.6 generation metadata | M4 | `test_report_contract.py::test_fr_7_6` | Planned |
| FR-8.1 review dispositions | M4 | `tests/integration/test_review_flow.py` | Planned |
| FR-8.2 reviewer/notes/timestamp persistence | M4 | `test_review_flow.py::test_fr_8_2_persisted` | Planned |
| FR-8.3 review performs no external action | M4 | `tests/security/test_no_execution_tools.py` | Planned |
| FR-8.4 conflicting review → 409 | M4 | `test_review_flow.py::test_fr_8_4_conflict` | Planned |
| FR-9.1 single error envelope | M1 | `tests/integration/test_error_envelope.py` | Planned |
| FR-9.2 health readiness | M1 | `tests/integration/test_health.py` | Planned |
| FR-10.1 evaluation harness table | M6 | `tests/evaluation/test_eval_harness.py` | Planned |
| FR-10.2 manual/assisted timings | M6 | `scripts/evaluate.py` + results fixture | Planned |
| FR-11.1 LangGraph persisted checkpoints | M3 | `tests/integration/test_graph_runtime.py` | Planned |
| FR-11.2 node failure degradation | M3 | `tests/integration/test_graph_faults.py` | Planned |
| FR-11.3 per-node timeout/retry | M3 | `test_graph_faults.py::test_fr_11_3` | Planned |
| FR-11.4 progress events | M3 | `test_graph_runtime.py::test_fr_11_4` | Planned |
| FR-12.1 three screens | M5 | `frontend/tests/ui.smoke.spec.ts` | Planned |
| FR-12.2 live/mock/skipped badges | M5 | `ui.smoke.spec.ts::badge_states` | Planned |
| FR-12.3 visible API/degraded failure | M5 | `ui.smoke.spec.ts::degraded_banner` | Planned |
| FR-13.1 one-command Docker Compose | M6 | `scripts/compose_smoke.ps1` + CI job | Planned |
| FR-13.2 pinned/idempotent seeds | M2/M6 | `tests/integration/test_seed_idempotency.py` | Planned |
| FR-13.3 complete README | M6 | `docs/quickstart-verification.md` | Planned |

## Non-functional requirements

| Requirement | Milestone | Verification | Status |
| --- | --- | --- | --- |
| NFR-01 localhost/secrets/limits | M1/M6 | compose inspection, `test_limits.py`, secret scan | Partial |
| NFR-02 read-only safety | M3/M4 | `test_no_execution_tools.py`, integration HTTP-method audit | Planned |
| NFR-03 evidence traceability | M2/M4 | `test_evidence_integrity.py` | Planned |
| NFR-04 degraded-report reliability | M3/M4 | `test_degradation_matrix.py` | Planned |
| NFR-05 performance | M6 | `bench/` results in evaluation report | Planned |
| NFR-06 layered imports | M1/M6 | `tests/unit/test_layering.py` | Planned |
| NFR-07 synthetic data only | M1/M6 | fixture audit + secret/indicator scan | Partial |
| NFR-08 reproducibility | M1/M6 | fresh-clone walkthrough | Planned |
| NFR-09 structured logs | M1 | `tests/integration/test_logging.py` | Planned |
| NFR-10 coverage/scenarios | M6 | coverage gate and evaluation harness | Planned |
| NFR-11 Windows/Linux portability | M1/M6 | PowerShell + Docker test matrix | Partial |
| NFR-12 provider/LLM cost control | M2/M3 | `test_budget.py`, call-count test | Planned |

## Milestone gate criteria

| Gate | Requirement | Evidence | Status |
| --- | --- | --- | --- |
| G1 | M1 alert round trip, ≥ 8 tests, clean Alembic upgrade | pytest report, Alembic run log | Pending |
| G2 | Scenario A = 29/low, timeline with reasons, all IP classes, timeout path | pytest + API transcript | Pending |
| G3 | LLM off, Scenario C = 84/high, valid report, ≥ 2 candidates, 100% evidence | CLI verification output | Pending |
| G4 | LLM on, validator pass, two-failure fallback, review persisted | pytest + API transcript | Pending |
| G5 | Browser demo, all UI states, ≥ 40 tests, ≥ 80% domain/service coverage | Playwright report + coverage XML | Pending |
| G6 | Fresh-clone under 15 min, evaluation table, clean secret/indicator scan | walkthrough + report | Pending |

## Scope guard

No requirement in this matrix authorises account blocking, host isolation, remediation
execution, LLM-computed scoring, or invented MITRE mappings. Those features are explicitly
out of scope for v1; absence is enforced by `test_no_execution_tools.py`.
