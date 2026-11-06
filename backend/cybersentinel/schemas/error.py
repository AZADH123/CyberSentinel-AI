"""Stable API error envelope."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """One field-level or context-specific error detail."""

    field: str | None = None
    issue: str


class ErrorBody(BaseModel):
    """Error body expected by every client."""

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    correlation_id: str


class ErrorEnvelope(BaseModel):
    """Top-level error response."""

    error: ErrorBody


def error_payload(
    *,
    code: str,
    message: str,
    correlation_id: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a plain dictionary for JSONResponse without bypassing validation rules."""
    return ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            correlation_id=correlation_id,
            details=[ErrorDetail(**detail) for detail in (details or [])],
        )
    ).model_dump(mode="json")
