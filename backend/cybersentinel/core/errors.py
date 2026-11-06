"""Application exceptions that map to the public error envelope.

Services and repositories raise ``AppError`` without importing FastAPI. The HTTP layer owns
serialisation, so business code stays testable without a web framework.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for expected, client-safe application failures."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []

    def __repr__(self) -> str:
        return f"AppError(status_code={self.status_code}, code={self.code!r})"


class NotFoundError(AppError):
    """A requested entity does not exist."""

    def __init__(self, entity: str, identifier: str) -> None:
        super().__init__(
            status_code=404,
            code="not_found",
            message=f"{entity} not found",
            details=[{"field": "id", "issue": f"unknown {entity}: {identifier}"}],
        )


class ConflictError(AppError):
    """A request conflicts with current state."""

    def __init__(
        self, code: str, message: str, details: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(status_code=409, code=code, message=message, details=details)


class InvalidRequestError(AppError):
    """A semantically invalid request after schema validation."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "validation_error",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(status_code=422, code=code, message=message, details=details)
