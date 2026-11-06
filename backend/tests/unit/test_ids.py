"""Identifier and time utility tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from cybersentinel.utils.ids import (
    is_uuid7,
    is_valid_ulid,
    new_investigation_id,
    new_ulid,
    new_uuid7,
    parse_incident_sequence,
)
from cybersentinel.utils.time import (
    format_rfc3339,
    is_too_old,
    parse_rfc3339,
    require_aware,
    to_utc_second,
    utc_now,
)


def test_new_uuid7_is_version_7() -> None:
    value = new_uuid7()
    assert isinstance(value, uuid.UUID)
    assert is_uuid7(value)


def test_new_ulid_round_trip_validation() -> None:
    value = new_ulid()
    assert len(value) == 26
    assert is_valid_ulid(value)
    assert not is_valid_ulid("INVALID!!")


def test_new_investigation_id_format() -> None:
    value = new_investigation_id()
    assert value.startswith("INV-")
    assert len(value) == 12
    assert int(value[4:], 16) >= 0


def test_parse_incident_sequence() -> None:
    assert parse_incident_sequence("INC-2026-0001", 2026) == 1
    assert parse_incident_sequence("INC-2025-0042", 2026) is None
    assert parse_incident_sequence("INC-2026-abc", 2026) is None


def test_require_aware_rejects_naive() -> None:
    naive = datetime(2026, 11, 3, 2, 30, 0)
    try:
        require_aware(naive)
    except ValueError as exc:
        assert "timezone" in str(exc)
    else:
        raise AssertionError("naive datetime must be rejected")


def test_to_utc_second_normalises_offset() -> None:
    value = datetime(2026, 11, 3, 2, 30, 0, 500000, tzinfo=UTC)
    normalised = to_utc_second(value)
    assert normalised.microsecond == 0
    assert normalised.tzinfo is not None


def test_rfc3339_round_trip() -> None:
    value = datetime(2026, 11, 3, 2, 30, 0, tzinfo=UTC)
    text = format_rfc3339(value)
    assert text.endswith("Z")
    assert parse_rfc3339(text) == value


def test_is_too_old_boundary() -> None:
    now = utc_now()
    assert is_too_old(now - timedelta(days=91), 90, now=now)
    assert not is_too_old(now - timedelta(days=89), 90, now=now)
