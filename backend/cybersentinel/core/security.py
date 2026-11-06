"""Security helpers shared by API, logging and integrations.

These functions contain no policy decisions about enrichment or scoring; they only redact,
truncate and validate values at trust boundaries.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Final

from cybersentinel.core.constants import PLACEHOLDER_SECRET_MARKERS

_SECRET_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"(?i)(api[_-]?key|token|authorization|secret)\s*[:=]\s*['\"]?([^\s,'\"]+)"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\b[a-f0-9]{64}\b"),
)

_REDACTED: Final[str] = "[REDACTED]"


def is_placeholder_secret(value: str | None) -> bool:
    """Return True for empty, short or obvious placeholder credentials."""
    if not value:
        return True
    lowered = value.strip().lower()
    return len(lowered) < 16 or any(marker in lowered for marker in PLACEHOLDER_SECRET_MARKERS)


def redact_text(value: str, limit: int = 4000) -> str:
    """Strip common secret shapes and bound log text length.

    The redaction is defence in depth, not a substitute for never logging secrets.
    """
    text = value[:limit]
    for pattern in _SECRET_PATTERNS:
        if pattern.groups >= 2:
            text = pattern.sub(lambda match: f"{match.group(1)}={_REDACTED}", text)
        else:
            text = pattern.sub(_REDACTED, text)
    return text


def redact_indicator(value: str) -> str:
    """Truncate an IP for diagnostic logs (/24 IPv4, /48 IPv6).

    Invalid values are replaced entirely rather than echoed back, because an arbitrary string
    may itself be sensitive.
    """
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return "[invalid-indicator]"
    if address.version == 4:
        network = ipaddress.ip_network(f"{address}/24", strict=False)
    else:
        network = ipaddress.ip_network(f"{address}/48", strict=False)
    return str(network)


def sanitise_header_value(value: str, limit: int = 200) -> str:
    """Remove control characters and bound a header value before logging."""
    cleaned = "".join(ch for ch in value if 32 <= ord(ch) < 127)
    return cleaned[:limit]


def constant_time_equals(left: str, right: str) -> bool:
    """Compare two strings without short-circuiting on the first differing byte."""
    import hmac

    return hmac.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
