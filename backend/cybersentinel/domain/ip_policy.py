"""IP eligibility policy (FR-4.1).

Determines whether an indicator may be submitted to a public reputation provider. The policy
is a pure function: no network, no environment, no database. Documentation, private, reserved
and other non-routeable ranges are always skipped so the prototype never abuses a provider.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from enum import StrEnum


class Eligibility(StrEnum):
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"


@dataclass(frozen=True)
class IpClassification:
    """Result of classifying one indicator."""

    eligible: bool
    reason_code: str | None
    canonical: str


_DOCUMENTATION_V4 = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
)
_DOCUMENTATION_V6 = (ipaddress.ip_network("2001:db8::/32"),)


def classify_ip(value: str) -> IpClassification:
    """Classify an IP literal for enrichment eligibility.

    Returns the canonical form even when the address is not eligible, so callers can store and
    display a stable value without performing a lookup.
    """
    try:
        address = ipaddress.ip_address(value.strip())
    except ValueError as exc:
        raise ValueError(f"invalid IP literal: {value!r}") from exc

    canonical = str(address)
    if address.is_private:
        return IpClassification(False, "private_range", canonical)
    if address.is_loopback:
        return IpClassification(False, "loopback", canonical)
    if address.is_link_local:
        return IpClassification(False, "link_local", canonical)
    if address.version == 4 and address in ipaddress.ip_network("100.64.0.0/10"):
        return IpClassification(False, "cgnat", canonical)
    if address.is_multicast:
        return IpClassification(False, "multicast", canonical)
    if address.is_reserved:
        return IpClassification(False, "reserved", canonical)
    if any(address in network for network in _DOCUMENTATION_V4) or any(
        address in network for network in _DOCUMENTATION_V6
    ):
        return IpClassification(False, "documentation_range", canonical)
    return IpClassification(True, None, canonical)
