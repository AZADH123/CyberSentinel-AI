"""Versioned, additive, capped risk model (FR-6.x, risk-v1).

Weights are embedded as a Python literal (the domain layer performs no I/O). A checked-in
``risk-v1.json`` is kept in sync as the human-readable reference; tests assert parity.
"""

from __future__ import annotations

from dataclasses import dataclass

from cybersentinel.domain import rules
from cybersentinel.domain.correlation import RelatedEvent

RISK_MODEL_VERSION = "risk-v1"

BAND_INFORMATIONAL = "informational"
BAND_LOW = "low"
BAND_MEDIUM = "medium"
BAND_HIGH = "high"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"

#: Documented weights kept in lock-step with backend/cybersentinel/domain/risk-v1.json.
RISK_WEIGHTS: dict[str, dict[str, int]] = {
    "R-01": {"burst_5_9": 8, "burst_10_19": 14, "burst_20_plus": 20},
    "R-02": {"success_3_4": 10, "success_5_plus": 20},
    "R-03": {"privileged": 8, "critical_asset": 8, "both": 15},
    "R-04": {"explicit_grant": 20, "ambiguous_change": 12},
    "R-05": {"malicious": 15, "suspicious": 8},
    "R-06": {"unusual_context": 10},
}


@dataclass(frozen=True)
class RiskFactor:
    """One contributing rule with its points and cited evidence."""

    rule_id: str
    label: str
    points: int
    signal: str | None
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class RiskAssessment:
    """A fully explained, additive score."""

    score: int
    band: str
    factors: tuple[RiskFactor, ...]
    confidence: str
    missing_signals: tuple[str, ...]
    risk_model_version: str


def band_for_score(score: int) -> str:
    if score <= 24:
        return BAND_INFORMATIONAL
    if score <= 49:
        return BAND_LOW
    if score <= 74:
        return BAND_MEDIUM
    return BAND_HIGH


def _enrichment_signal(enrichment: list[dict]) -> tuple[str | None, tuple[str, ...]]:
    """Extract the strongest reputation signal and its evidence references."""
    signal: str | None = None
    evidence: tuple[str, ...] = ()
    priority = {"malicious": 3, "suspicious": 2, "clean": 1}
    for item in enrichment:
        candidate = item.get("signal")
        if candidate and priority.get(candidate, 0) > priority.get(signal or "", 0):
            signal = candidate
            evidence = tuple(item.get("evidence_refs", []))
    return signal, evidence


def compute_risk(
    anchor: dict,
    findings: list[rules.Finding],
    related_events: list[RelatedEvent],
    enrichment: list[dict],
    *,
    gaps: list[str],
    risk_model_version: str = RISK_MODEL_VERSION,
) -> RiskAssessment:
    """Compute the additive 0-100 score with a per-factor breakdown."""
    factors: list[RiskFactor] = []

    for finding in findings:
        factors.append(
            RiskFactor(
                rule_id=finding.rule_id,
                label=finding.summary,
                points=finding.points,
                signal=None,
                evidence_refs=finding.evidence_refs,
            )
        )

    # R-02: success following a failure burst within the correlation window.
    failure_count = int(anchor.get("failure_count", 0))
    successes_after = [
        item.event
        for item in related_events
        if item.event.get("outcome") == "success"
        and item.event.get("event_time", anchor["event_time"]) > anchor["event_time"]
    ]
    if successes_after and failure_count >= 5:
        points = (
            RISK_WEIGHTS["R-02"]["success_5_plus"]
            if failure_count >= 5
            else RISK_WEIGHTS["R-02"]["success_3_4"]
        )
        factors.append(
            RiskFactor(
                rule_id="R-02",
                label=f"Successful authentication followed a {failure_count}-failure burst",
                points=points,
                signal="success_after_burst",
                evidence_refs=(successes_after[0].get("evidence_key", ""),),
            )
        )

    # R-04: privilege change observed among related account-change events.
    for item in related_events:
        candidate = item.event
        if candidate.get("event_type") == "account_change":
            change_kind = candidate.get("change_kind", candidate.get("action", ""))
            explicit = change_kind in {"role_grant", "group_add", "privilege_grant"}
            points = (
                RISK_WEIGHTS["R-04"]["explicit_grant"]
                if explicit
                else RISK_WEIGHTS["R-04"]["ambiguous_change"]
            )
            factors.append(
                RiskFactor(
                    rule_id="R-04",
                    label=f"Privilege change: {change_kind}",
                    points=points,
                    signal="privilege_change",
                    evidence_refs=(candidate.get("evidence_key", ""),),
                )
            )

    # R-05: external reputation of an eligible indicator.
    enrichment_signal, enrichment_evidence = _enrichment_signal(enrichment)
    if enrichment_signal == "malicious":
        factors.append(
            RiskFactor(
                rule_id="R-05",
                label="Malicious reputation result from threat intelligence",
                points=RISK_WEIGHTS["R-05"]["malicious"],
                signal="malicious",
                evidence_refs=enrichment_evidence,
            )
        )
    elif enrichment_signal == "suspicious":
        factors.append(
            RiskFactor(
                rule_id="R-05",
                label="Suspicious reputation result from threat intelligence",
                points=RISK_WEIGHTS["R-05"]["suspicious"],
                signal="suspicious",
                evidence_refs=enrichment_evidence,
            )
        )

    # R-06: first-seen public IP for a user with prior event history.
    prior_same_user = [
        item.event
        for item in related_events
        if str(item.event.get("username", "")).casefold()
        == str(anchor.get("username", "")).casefold()
    ]
    first_seen = not any(
        item.get("source_ip") == anchor.get("source_ip") for item in prior_same_user
    )
    if first_seen and len(prior_same_user) >= 5 and anchor.get("source_ip_public", False):
        factors.append(
            RiskFactor(
                rule_id="R-06",
                label="First-seen public source address with prior user history",
                points=RISK_WEIGHTS["R-06"]["unusual_context"],
                signal="first_seen_public_ip",
                evidence_refs=tuple(
                    item.get("evidence_key", "") for item in prior_same_user[:1]
                ),
            )
        )

    raw = sum(factor.points for factor in factors)
    score = min(raw, 100)
    band = band_for_score(score)

    confidence = _confidence(gaps, enrichment_signal, related_events)
    missing = tuple(gaps)
    return RiskAssessment(
        score=score,
        band=band,
        factors=tuple(factors),
        confidence=confidence,
        missing_signals=missing,
        risk_model_version=risk_model_version,
    )


def _confidence(gaps: list[str], enrichment_signal: str | None, related: list[RelatedEvent]) -> str:
    gap_count = len(gaps)
    if enrichment_signal in {None, "unavailable", "skipped"} and not related:
        return CONFIDENCE_LOW
    if gap_count >= 2:
        return CONFIDENCE_LOW
    if gap_count == 1:
        return CONFIDENCE_MEDIUM
    return CONFIDENCE_HIGH
