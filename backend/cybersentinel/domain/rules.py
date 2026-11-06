"""Deterministic triage rules (FR-2.x, R-01, R-03, R-04).

The rules produce named findings with points and evidence references. Absence of data never
produces points; it produces a gap entry elsewhere. Free text in ``raw_event`` is never read
here, which is the structural defence against prompt injection.
"""

from __future__ import annotations

from dataclasses import dataclass

CLAIM_OBSERVED = "observed"
CLAIM_INFERRED = "inferred"

#: Usernames treated as privileged for the local, synthetic corpus. This is a curated heuristic,
#: not an identity-provider lookup; it is documented as a prototype limitation.
PRIVILEGED_USERNAMES: frozenset[str] = frozenset(
    {"admin", "administrator", "root", "superuser", "backup", "service-admin"}
)


@dataclass(frozen=True)
class Finding:
    """A deterministic triage finding."""

    rule_id: str
    summary: str
    points: int
    claim_type: str
    evidence_refs: tuple[str, ...]


def is_privileged_username(username: str) -> bool:
    """Return True for a curated privileged username or ``admin`` prefix."""
    lowered = username.casefold()
    return lowered in PRIVILEGED_USERNAMES or lowered.startswith("admin")


def is_critical_asset(asset_criticality: str) -> bool:
    """Treat ``high`` and ``critical`` assets as high-value (matches the worked examples)."""
    return asset_criticality in {"high", "critical"}


def failure_burst_points(failure_count: int) -> int | None:
    """Return R-01 points for a failure count, or None below the threshold."""
    if 5 <= failure_count <= 9:
        return 8
    if 10 <= failure_count <= 19:
        return 14
    if failure_count >= 20:
        return 20
    return None


def privilege_asset_points(username: str, asset_criticality: str) -> int | None:
    """Return R-03 points, or None when neither privileged nor high-value."""
    privileged = is_privileged_username(username)
    critical = is_critical_asset(asset_criticality)
    if privileged and critical:
        return 15
    if privileged:
        return 8
    if critical:
        return 8
    return None


def privilege_change_points(change_kind: str) -> int:
    """Return R-04 points for an account-change event kind."""
    if change_kind in {"role_grant", "group_add", "privilege_grant"}:
        return 20
    return 12


def triage(event: dict, alert_evidence_key: str) -> list[Finding]:
    """Evaluate anchor-observable rules for a normalised event.

    Args:
        event: Normalised event dict with ``outcome``, ``failure_count``, ``username``,
            ``asset_criticality`` and optionally ``event_type``/``action``.
        alert_evidence_key: Evidence key (e.g. ``EV-001``) for the alert field record.
    """
    findings: list[Finding] = []
    evidence = (alert_evidence_key,)

    if event.get("outcome") == "failure":
        points = failure_burst_points(int(event.get("failure_count", 0)))
        if points is not None:
            findings.append(
                Finding(
                    rule_id="R-01",
                    summary=(
                        f"{event.get('failure_count')} authentication failures recorded "
                        f"for {event.get('username')} at {event.get('host')}"
                    ),
                    points=points,
                    claim_type=CLAIM_OBSERVED,
                    evidence_refs=evidence,
                )
            )

    privilege_points = privilege_asset_points(
        str(event.get("username", "")), str(event.get("asset_criticality", "medium"))
    )
    if privilege_points is not None:
        findings.append(
            Finding(
                rule_id="R-03",
                summary=(
                    f"{event.get('username')} is a privileged identity on a "
                    f"{event.get('asset_criticality')} asset"
                ),
                points=privilege_points,
                claim_type=CLAIM_OBSERVED,
                evidence_refs=evidence,
            )
        )

    if event.get("event_type") == "account_change":
        change_kind = str(event.get("change_kind", event.get("action", "")))
        findings.append(
            Finding(
                rule_id="R-04",
                summary=f"Account privilege change observed: {change_kind}",
                points=privilege_change_points(change_kind),
                claim_type=CLAIM_OBSERVED,
                evidence_refs=evidence,
            )
        )

    return findings
