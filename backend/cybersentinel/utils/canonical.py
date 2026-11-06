"""Canonical JSON and hashing helpers.

Evidence checksums and request/idempotency fingerprints depend on a stable byte
representation: UTF-8, sorted keys, compact separators and normalised UTC timestamps.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        normalised = value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        return normalised.isoformat(timespec="seconds").replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"object of type {type(value).__name__} is not canonical-JSON serialisable")


def canonical_json(value: Any) -> str:
    """Serialise a value to deterministic compact JSON."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_json_default,
    )


def canonical_bytes(value: Any) -> bytes:
    """Return canonical JSON encoded as UTF-8 bytes."""
    return canonical_json(value).encode("utf-8")


def sha256_hex(value: Any) -> str:
    """Hash a canonical JSON value with SHA-256 and return lowercase hex."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_text(value: str) -> str:
    """Hash a UTF-8 string with SHA-256."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_sha256(value: Any, expected_hex: str) -> bool:
    """Constant-time integrity comparison for a canonical value."""
    import hmac

    actual = sha256_hex(value)
    return hmac.compare_digest(actual, expected_hex.lower())
