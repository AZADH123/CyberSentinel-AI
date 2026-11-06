"""Identifier generation following the PRD conventions.

UUIDv7 keeps alert keys time-ordered without exposing a business sequence. ULIDs are used only
for request correlation. Both are generated locally with the standard library.
"""

from __future__ import annotations

import secrets
import time
import uuid
from typing import Final

_CROCKFORD: Final[str] = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CROCKFORD_INDEX: Final[dict[str, int]] = {char: index for index, char in enumerate(_CROCKFORD)}

# UUIDv7 bit layout (RFC 9562): 48-bit Unix ms | version 7 | 12 random bits |
# variant 10 | 62 random bits.
_UUID7_TIME_BITS = 48
_UUID7_RAND_A_BITS = 12
_UUID7_RAND_B_BITS = 62


def _encode_crockford(value: int, length: int) -> str:
    chars = ["0"] * length
    for index in range(length - 1, -1, -1):
        chars[index] = _CROCKFORD[value & 0x1F]
        value >>= 5
    if value:
        raise ValueError("value does not fit in the requested ULID length")
    return "".join(chars)


def new_ulid(timestamp_ms: int | None = None) -> str:
    """Generate a 26-character Crockford-base32 ULID.

    The generator is not strictly monotonic within a millisecond, which is acceptable for a
    request correlation identifier. It is always 128 bits of encoded time + randomness.
    """
    millis = timestamp_ms if timestamp_ms is not None else time.time_ns() // 1_000_000
    if millis < 0 or millis >= 1 << _UUID7_TIME_BITS:
        raise ValueError("timestamp outside the ULID 48-bit millisecond range")
    randomness = secrets.randbits(80)
    return _encode_crockford(millis, 10) + _encode_crockford(randomness, 16)


def is_valid_ulid(value: str) -> bool:
    """Return True for a syntactically valid 26-character ULID."""
    if len(value) != 26:
        return False
    try:
        for char in value.upper():
            _CROCKFORD_INDEX[char]
    except KeyError:
        return False
    return True


def new_uuid7() -> uuid.UUID:
    """Generate an RFC 9562 UUID version 7 using time and cryptographic randomness."""
    millis = time.time_ns() // 1_000_000
    if millis < 0 or millis >= 1 << _UUID7_TIME_BITS:
        raise ValueError("clock outside the UUIDv7 48-bit millisecond range")
    value = millis << 80
    value |= 0x7 << 76
    value |= secrets.randbits(_UUID7_RAND_A_BITS) << 64
    value |= 0b10 << 62
    value |= secrets.randbits(_UUID7_RAND_B_BITS)
    return uuid.UUID(int=value)


def is_uuid7(value: uuid.UUID) -> bool:
    """Return True when a UUID uses version 7 and the RFC variant."""
    return value.version == 7 and value.variant == uuid.RFC_4122


def new_investigation_id() -> str:
    """Generate an investigation identifier of the form ``INV-9F2A41C8``."""
    return f"INV-{secrets.token_hex(4).upper()}"


def parse_incident_sequence(incident_id: str, year: int) -> int | None:
    """Parse the numeric suffix of a well-formed incident identifier."""
    prefix = f"INC-{year}-"
    if not incident_id.startswith(prefix):
        return None
    suffix = incident_id.removeprefix(prefix)
    if len(suffix) != 4 or not suffix.isdigit():
        return None
    return int(suffix)
