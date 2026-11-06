"""Structured JSON logging with request correlation.

No request body, credential, provider payload or full public indicator is emitted. The
correlation ID is held in a context variable and attached to every record automatically.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from cybersentinel.core.security import redact_text

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(value: str) -> None:
    """Bind the current request correlation ID to this execution context."""
    _correlation_id.set(value)


def get_correlation_id() -> str | None:
    """Return the correlation ID bound to the current execution context."""
    return _correlation_id.get()


def clear_correlation_id() -> None:
    """Clear the correlation ID for the current execution context."""
    _correlation_id.set(None)


class JsonFormatter(logging.Formatter):
    """Render one redacted JSON object per log line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_text(record.getMessage()),
            "correlation_id": get_correlation_id(),
        }
        for field in ("method", "path", "status_code", "duration_ms", "event", "node"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = redact_text(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, default=str)


class PlainFormatter(logging.Formatter):
    """Human-friendly local formatter that still redacts message text."""

    def format(self, record: logging.LogRecord) -> str:
        correlation = get_correlation_id() or "-"
        message = redact_text(record.getMessage())
        base = (
            f"{datetime.now(UTC).isoformat(timespec='seconds')} "
            f"{record.levelname:<8} [{correlation}] {record.name}: {message}"
        )
        if record.exc_info:
            base += "\n" + redact_text(self.formatException(record.exc_info))
        return base


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    """Configure process logging once, replacing default handlers."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter() if json_output else PlainFormatter())
    root.addHandler(handler)

    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(max(logging.WARNING, root.level))
