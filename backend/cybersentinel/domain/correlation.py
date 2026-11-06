"""Event correlation (FR-3.x).

Pure matching arithmetic: no SQL, no I/O. The repository passes candidate rows in; this module
decides which are related and why.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class RelatedEvent:
    """One correlated event with machine-readable match reasons."""

    event: dict
    match_reasons: tuple[str, ...]
    match_strength: int


def _matches(anchor: dict, candidate: dict) -> tuple[tuple[str, ...], int]:
    reasons: list[str] = []
    strength = 0
    if str(candidate.get("username", "")).casefold() == str(
        anchor.get("username", "")
    ).casefold():
        reasons.append("same_username")
        strength += 2
    if candidate.get("source_ip") == anchor.get("source_ip"):
        reasons.append("same_source_ip")
        strength += 2
    if candidate.get("host") == anchor.get("host"):
        reasons.append("same_host")
        strength += 1
    return tuple(reasons), strength


def correlate(
    anchor: dict,
    candidates: list[dict],
    *,
    window: timedelta,
    limit: int = 200,
) -> list[RelatedEvent]:
    """Return chronological related events within ``window`` of the anchor.

    The anchor itself is excluded by ID. Matching is bounded to ``limit`` events and is
    read-only: no mutation of inputs or external state.
    """
    anchor_time: datetime = anchor["event_time"]
    lower = anchor_time - window
    upper = anchor_time + window
    anchor_id = anchor.get("id")

    related: list[RelatedEvent] = []
    for candidate in candidates:
        if candidate.get("id") == anchor_id:
            continue
        event_time = candidate.get("event_time")
        if not isinstance(event_time, datetime) or not (lower <= event_time <= upper):
            continue
        reasons, strength = _matches(anchor, candidate)
        if not reasons:
            continue
        related.append(
            RelatedEvent(event=candidate, match_reasons=reasons, match_strength=strength)
        )

    related.sort(key=lambda item: item.event["event_time"])
    return related[:limit]
