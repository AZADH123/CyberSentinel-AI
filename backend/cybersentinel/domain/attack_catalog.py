"""Curated MITRE ATT&CK catalogue (FR-5.x).

Only technique IDs present in this allowlist may enter a report. Candidates are *possible*
mappings, never confirmed attribution, and each must cite at least one evidence reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

ATTACK_CATALOGUE_VERSION = "attack-subset-1.0"


class Tactic(StrEnum):
    CREDENTIAL_ACCESS = "Credential Access"
    DEFENSE_EVASION = "Defense Evasion"
    PERSISTENCE = "Persistence"
    INITIAL_ACCESS = "Initial Access"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    LATERAL_MOVEMENT = "Lateral Movement"


@dataclass(frozen=True)
class Technique:
    """A vendored ATT&CK technique entry."""

    technique_id: str
    name: str
    tactic: str


TECHNIQUES: dict[str, Technique] = {
    "T1110": Technique("T1110", "Brute Force", Tactic.CREDENTIAL_ACCESS.value),
    "T1110.003": Technique("T1110.003", "Password Spraying", Tactic.CREDENTIAL_ACCESS.value),
    "T1078": Technique("T1078", "Valid Accounts", Tactic.DEFENSE_EVASION.value),
    "T1078.004": Technique("T1078.004", "Cloud Accounts", Tactic.DEFENSE_EVASION.value),
    "T1133": Technique("T1133", "External Remote Services", Tactic.INITIAL_ACCESS.value),
    "T1098": Technique("T1098", "Account Manipulation", Tactic.PERSISTENCE.value),
    "T1021": Technique("T1021", "Remote Services", Tactic.LATERAL_MOVEMENT.value),
    "T1021.001": Technique("T1021.001", "Remote Desktop Protocol", Tactic.LATERAL_MOVEMENT.value),
}


@dataclass(frozen=True)
class AttackCandidate:
    """A validated candidate mapping with rationale and evidence."""

    technique_id: str
    technique_name: str
    tactic: str
    confidence: str
    rationale: str
    evidence_refs: tuple[str, ...]
    url: str


def technique_url(technique_id: str) -> str:
    """Build the canonical MITRE URL from the validated ID only."""
    return f"https://attack.mitre.org/techniques/{technique_id}/"


def map_attack(
    anchor: dict,
    findings: list,
    related_events: list,
) -> list[AttackCandidate]:
    """Rule-driven candidate mapping, capped at five and ordered by confidence/evidence.

    Args:
        anchor: Normalised anchor event dict.
        findings: Triage findings (objects with ``rule_id`` and ``evidence_refs``).
        related_events: Correlated ``RelatedEvent`` instances.
    """
    candidates: list[AttackCandidate] = []
    failure_count = int(anchor.get("failure_count", 0))
    usernames = {str(item.event.get("username", "")).casefold() for item in related_events}
    usernames.add(str(anchor.get("username", "")).casefold())
    successes = [item.event for item in related_events if item.event.get("outcome") == "success"]
    anchor_evidence = (anchor.get("evidence_key", ""),)

    # Brute force: >= 10 failures against one account.
    if failure_count >= 10:
        candidates.append(
            AttackCandidate(
                technique_id="T1110",
                technique_name=TECHNIQUES["T1110"].name,
                tactic=TECHNIQUES["T1110"].tactic,
                confidence="medium",
                rationale=f"{failure_count} failures against a single account within the window",
                evidence_refs=anchor_evidence,
                url=technique_url("T1110"),
            )
        )

    # Password spraying: failures against >= 5 distinct usernames from one IP.
    if failure_count >= 5 and len(usernames) >= 5:
        candidates.append(
            AttackCandidate(
                technique_id="T1110.003",
                technique_name=TECHNIQUES["T1110.003"].name,
                tactic=TECHNIQUES["T1110.003"].tactic,
                confidence="medium",
                rationale="Failures observed against five or more distinct usernames",
                evidence_refs=anchor_evidence,
                url=technique_url("T1110.003"),
            )
        )

    # Valid accounts: success following >= 5 failures.
    if successes and failure_count >= 5:
        candidates.append(
            AttackCandidate(
                technique_id="T1078",
                technique_name=TECHNIQUES["T1078"].name,
                tactic=TECHNIQUES["T1078"].tactic,
                confidence="medium",
                rationale="Successful authentication followed a multi-failure burst",
                evidence_refs=(successes[0].get("evidence_key", ""),),
                url=technique_url("T1078"),
            )
        )

    # External remote services: external IP authenticating to a VPN/remote-access host.
    if anchor.get("source_ip_public", False) and (
        "vpn" in str(anchor.get("host", "")).casefold()
        or "remote" in str(anchor.get("host", "")).casefold()
    ):
        candidates.append(
            AttackCandidate(
                technique_id="T1133",
                technique_name=TECHNIQUES["T1133"].name,
                tactic=TECHNIQUES["T1133"].tactic,
                confidence="low",
                rationale="External source authenticating to a remote-access host",
                evidence_refs=anchor_evidence,
                url=technique_url("T1133"),
            )
        )

    # Account manipulation: account-change event among related events.
    for item in related_events:
        if item.event.get("event_type") == "account_change":
            candidates.append(
                AttackCandidate(
                    technique_id="T1098",
                    technique_name=TECHNIQUES["T1098"].name,
                    tactic=TECHNIQUES["T1098"].tactic,
                    confidence="medium",
                    rationale="Privileged group membership change observed",
                    evidence_refs=(item.event.get("evidence_key", ""),),
                    url=technique_url("T1098"),
                )
            )

    # Order by confidence weight then keep at most five.
    order = {"high": 3, "medium": 2, "low": 1}
    candidates.sort(
        key=lambda candidate: (-order[candidate.confidence], -len(candidate.evidence_refs))
    )
    return candidates[:5]
