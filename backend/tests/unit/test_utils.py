"""Canonical JSON, hashing and security helper tests."""

from __future__ import annotations

from datetime import UTC, datetime

from cybersentinel.core.security import (
    is_placeholder_secret,
    redact_indicator,
    redact_text,
)
from cybersentinel.utils.canonical import canonical_json, sha256_hex, verify_sha256


def test_canonical_json_is_key_order_independent() -> None:
    left = {"a": 1, "b": [1, 2, 3]}
    right = {"b": [1, 2, 3], "a": 1}
    assert canonical_json(left) == canonical_json(right)
    assert sha256_hex(left) == sha256_hex(right)


def test_canonical_json_normalises_datetime() -> None:
    first = {"when": datetime(2026, 11, 3, 2, 30, 0, tzinfo=UTC)}
    second = {"when": "2026-11-03T02:30:00Z"}
    assert sha256_hex(first) == sha256_hex(second)


def test_verify_sha256_detects_tampering() -> None:
    value = {"evidence": 1}
    digest = sha256_hex(value)
    assert verify_sha256(value, digest)
    assert not verify_sha256({"evidence": 2}, digest)


def test_redact_indicator_truncates_ipv4() -> None:
    assert redact_indicator("198.51.100.24") == "198.51.100.0/24"
    assert redact_indicator("not-an-ip") == "[invalid-indicator]"


def test_redact_text_strips_api_keys() -> None:
    assert "AIza" not in redact_text("authorization=AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ01234")


def test_placeholder_secret_detection() -> None:
    assert is_placeholder_secret("change-me")
    assert is_placeholder_secret("short")
    assert not is_placeholder_secret("a-32-character-random-key-000000000")
