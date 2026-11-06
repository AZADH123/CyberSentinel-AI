"""Stable application constants.

Values that form part of an external contract (enumerations, limits, versions) live here so
the API, database models and tests share one definition.
"""

from __future__ import annotations

from enum import StrEnum

APP_NAME = "CyberSentinel AI"
APP_VERSION = "0.1.0"
API_PREFIX = "/api/v1"
REPORT_SCHEMA_VERSION = "1.0.0"
RISK_MODEL_VERSION = "risk-v1"


class EventType(StrEnum):
    """Event families accepted by the v1 ingestion contract."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ACCOUNT_CHANGE = "account_change"


class Outcome(StrEnum):
    """Normalised authentication outcome."""

    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


class AssetCriticality(StrEnum):
    """Asset importance supplied by the source or defaulted at ingestion."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    """Analyst-facing incident lifecycle."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    AWAITING_REVIEW = "awaiting_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    FAILED = "failed"


class Severity(StrEnum):
    """Severity bands independent of the numeric score representation."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Confidence(StrEnum):
    """Qualitative evidence-completeness statement, never a probability."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EnrichmentMode(StrEnum):
    """Available threat-intelligence modes."""

    LIVE = "live"
    MOCK = "mock"
    OFF = "off"


class EnrichmentStatus(StrEnum):
    """Provider outcome recorded for every attempted or skipped indicator."""

    OK = "ok"
    MOCK = "mock"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    BUDGET_EXHAUSTED = "budget_exhausted"


class InvestigationStatus(StrEnum):
    """Execution lifecycle for a graph run."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_DEGRADED = "completed_degraded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class Disposition(StrEnum):
    """Human review decision."""

    ACCEPT = "accept"
    REJECT = "reject"
    ESCALATE = "escalate"


VALID_EVENT_TYPES: frozenset[str] = frozenset(item.value for item in EventType)
VALID_OUTCOMES: frozenset[str] = frozenset(item.value for item in Outcome)
VALID_CRITICALITIES: frozenset[str] = frozenset(item.value for item in AssetCriticality)
VALID_INCIDENT_STATUSES: frozenset[str] = frozenset(item.value for item in IncidentStatus)
VALID_SEVERITIES: frozenset[str] = frozenset(item.value for item in Severity)
VALID_CONFIDENCES: frozenset[str] = frozenset(item.value for item in Confidence)
VALID_DISPOSITIONS: frozenset[str] = frozenset(item.value for item in Disposition)
VALID_ENRICHMENT_STATUSES: frozenset[str] = frozenset(item.value for item in EnrichmentStatus)
VALID_INVESTIGATION_STATUSES: frozenset[str] = frozenset(
    item.value for item in InvestigationStatus
)

MIN_FAILURE_COUNT = 0
MAX_FAILURE_COUNT = 10_000
MAX_RAW_EVENT_BYTES = 16 * 1024
MAX_RAW_EVENT_DEPTH = 5
MAX_RAW_EVENT_KEY_LENGTH = 64
MAX_REQUEST_BYTES = 262_144
CORRELATION_WINDOW_MINUTES = 30
CORRELATION_MAX_EVENTS = 200
NEAR_DUPLICATE_WINDOW_SECONDS = 60

#: Placeholder key fragments rejected when live external providers are enabled.
PLACEHOLDER_SECRET_MARKERS: tuple[str, ...] = (
    "changeme",
    "change-me",
    "replace-me",
    "replace_me",
    "your-key",
    "your_key",
    "demo-key",
    "example",
)
