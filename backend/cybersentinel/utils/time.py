"""UTC time helpers.

Every stored timestamp is timezone-aware UTC with second precision. Naive values are rejected
at the trust boundary rather than silently assumed to be local time.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(UTC)


def require_aware(value: datetime) -> datetime:
    """Return an aware datetime converted to UTC, or raise ``ValueError``."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone offset required")
    return value.astimezone(UTC)


def to_utc_second(value: datetime) -> datetime:
    """Normalise an aware datetime to UTC with zero microseconds."""
    return require_aware(value).replace(microsecond=0)


def format_rfc3339(value: datetime) -> str:
    """Format an aware datetime as RFC 3339 UTC with a ``Z`` suffix."""
    return to_utc_second(value).isoformat().replace("+00:00", "Z")


def parse_rfc3339(value: str) -> datetime:
    """Parse an RFC 3339 timestamp and require an explicit offset."""
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    parsed = datetime.fromisoformat(candidate)
    return to_utc_second(parsed)


def is_too_old(value: datetime, max_age_days: int, now: datetime | None = None) -> bool:
    """Whether an event is older than the configured ingestion age limit."""
    reference = now or utc_now()
    return to_utc_second(value) < to_utc_second(reference) - timedelta(days=max_age_days)


def is_too_far_future(
    value: datetime, now: datetime | None = None, tolerance: timedelta | None = None
) -> bool:
    """Whether an event exceeds the allowed future clock skew (default +5 minutes)."""
    reference = now or utc_now()
    return to_utc_second(value) > to_utc_second(reference) + (tolerance or timedelta(minutes=5))
