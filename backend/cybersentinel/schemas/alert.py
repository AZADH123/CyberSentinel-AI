"""Alert ingestion and read contracts, enforcing PRD §9.1 field rules."""

from __future__ import annotations

import re
from datetime import datetime
from ipaddress import ip_address
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cybersentinel.core.constants import (
    MAX_FAILURE_COUNT,
    MAX_RAW_EVENT_BYTES,
    MAX_RAW_EVENT_DEPTH,
    MAX_RAW_EVENT_KEY_LENGTH,
    MIN_FAILURE_COUNT,
    AssetCriticality,
    EventType,
    IncidentStatus,
    Outcome,
    Severity,
)
from cybersentinel.schemas.incident import IncidentSummary
from cybersentinel.utils.canonical import canonical_json, sha256_hex
from cybersentinel.utils.time import (
    format_rfc3339,
    is_too_far_future,
    is_too_old,
    to_utc_second,
)

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_SOURCE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_HOST_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]*$")


def _validate_raw_event(value: Any, depth: int = 1) -> None:
    """Recursively enforce depth, key length and string-size constraints."""
    if depth > MAX_RAW_EVENT_DEPTH:
        raise ValueError(f"raw_event nesting depth must not exceed {MAX_RAW_EVENT_DEPTH}")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("raw_event keys must be strings")
            if len(key) > MAX_RAW_EVENT_KEY_LENGTH:
                raise ValueError(
                    f"raw_event keys must be <= {MAX_RAW_EVENT_KEY_LENGTH} characters"
                )
            _validate_raw_event(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _validate_raw_event(item, depth + 1)
    elif isinstance(value, str) and len(value.encode("utf-8")) > MAX_RAW_EVENT_BYTES:
        raise ValueError(f"raw_event strings must be <= {MAX_RAW_EVENT_BYTES} bytes")


class AlertCreate(BaseModel):
    """Validated authentication alert payload."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source: str = Field(min_length=1, max_length=64, pattern=_SOURCE_PATTERN.pattern)
    event_type: EventType
    event_time: datetime
    username: str = Field(min_length=1, max_length=128)
    source_ip: str
    host: str = Field(min_length=1, max_length=253, pattern=_HOST_PATTERN.pattern)
    outcome: Outcome
    failure_count: int | None = Field(
        default=None, ge=MIN_FAILURE_COUNT, le=MAX_FAILURE_COUNT
    )
    asset_criticality: AssetCriticality = AssetCriticality.MEDIUM
    raw_event: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("source", "host", mode="before")
    @classmethod
    def lowercase_identifiers(cls, value: object) -> object:
        return value.lower() if isinstance(value, str) else value

    @field_validator("username")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if _CONTROL_CHARS.search(value):
            raise ValueError("username must not contain control characters")
        return value

    @field_validator("source_ip")
    @classmethod
    def canonical_ip_literal(cls, value: str) -> str:
        try:
            return str(ip_address(value.strip()))
        except ValueError as exc:
            raise ValueError("source_ip must be a valid IPv4 or IPv6 literal") from exc

    @field_validator("event_time")
    @classmethod
    def timezone_aware_and_recent(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timezone offset required")
        if is_too_far_future(value):
            raise ValueError("event_time must not be more than 5 minutes in the future")
        if is_too_old(value, max_age_days=90):
            raise ValueError("event_time must not be older than 90 days")
        return to_utc_second(value)

    @field_validator("raw_event")
    @classmethod
    def bounded_raw_event(cls, value: dict[str, Any]) -> dict[str, Any]:
        _validate_raw_event(value)
        if len(canonical_json(value).encode("utf-8")) > MAX_RAW_EVENT_BYTES:
            raise ValueError(f"raw_event must be <= {MAX_RAW_EVENT_BYTES} bytes")
        return value

    @field_validator("idempotency_key")
    @classmethod
    def printable_idempotency_key(cls, value: str | None) -> str | None:
        if value is not None and _CONTROL_CHARS.search(value):
            raise ValueError("idempotency_key must not contain control characters")
        return value

    @model_validator(mode="after")
    def default_failure_count(self) -> AlertCreate:
        """Materialise the documented default without losing whether it was supplied."""
        if self.failure_count is None:
            self.failure_count = 0
        return self

    @property
    def input_gaps(self) -> list[str]:
        """Fields absent from the request that reduce confidence later."""
        gaps: list[str] = []
        if "asset_criticality" not in self.model_fields_set:
            gaps.append("asset_criticality defaulted to medium")
        if "failure_count" not in self.model_fields_set:
            gaps.append("failure_count was not supplied; defaulted to 0")
        return gaps

    def normalized(self) -> dict[str, Any]:
        """Return the canonical, queryable normalised event."""
        return {
            "source": self.source,
            "event_type": self.event_type.value,
            "action": self.event_type.value,
            "event_time": format_rfc3339(self.event_time),
            "username": self.username,
            "source_ip": self.source_ip,
            "host": self.host,
            "outcome": self.outcome.value,
            "failure_count": self.failure_count,
            "asset_criticality": self.asset_criticality.value,
            "input_gaps": self.input_gaps,
        }

    def stored_raw_payload(self) -> dict[str, Any]:
        """Return the complete validated request as JSON for the immutable raw column."""
        return self.model_dump(mode="json")

    def dedupe_hash(self) -> str:
        """Hash the fields that define a near-duplicate event."""
        return sha256_hex(
            {
                "source": self.source,
                "event_type": self.event_type.value,
                "event_time": format_rfc3339(self.event_time),
                "username": self.username.casefold(),
                "source_ip": self.source_ip,
                "host": self.host,
                "outcome": self.outcome.value,
            }
        )

    def request_fingerprint(self) -> str:
        """Hash the full request (excluding the key itself) for idempotency conflict checks."""
        payload = self.model_dump(mode="json", exclude={"idempotency_key"})
        return sha256_hex(payload)


class AlertCreateResponse(BaseModel):
    """Response returned by alert ingestion for both create and replay."""

    alert_id: str
    incident_id: str
    status: IncidentStatus
    event_time: datetime
    created_at: datetime
    duplicate_of: str | None = None


class NormalizedEventView(BaseModel):
    """Normalised event projection."""

    model_config = ConfigDict(extra="allow")

    source: str
    event_type: EventType
    action: str
    event_time: datetime
    username: str
    source_ip: str
    host: str
    outcome: Outcome
    failure_count: int
    asset_criticality: AssetCriticality
    input_gaps: list[str] = Field(default_factory=list)


class AlertDetail(BaseModel):
    """Alert detail with raw payload, normalised event and linked incident."""

    alert_id: str
    source: str
    event_type: EventType
    event_time: datetime
    raw_event: dict[str, Any]
    normalized_event: NormalizedEventView
    incident: IncidentSummary
    duplicate_of: str | None
    created_at: datetime


class AlertListItem(BaseModel):
    """Alert queue row."""

    alert_id: str
    source: str
    event_type: EventType
    event_time: datetime
    username: str
    source_ip: str
    host: str
    outcome: Outcome
    failure_count: int
    severity: Severity
    risk_score: int
    status: IncidentStatus
    confidence: str
    created_at: datetime


class AlertListResponse(BaseModel):
    """Cursor-paginated alerts."""

    items: list[AlertListItem]
    next_cursor: str | None = None
