"""Centralised exception handlers producing the single API error envelope."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from cybersentinel.api.middleware.correlation import correlation_for_request
from cybersentinel.core.errors import AppError
from cybersentinel.core.logging import get_correlation_id
from cybersentinel.schemas.error import error_payload
from cybersentinel.utils.ids import new_ulid

logger = logging.getLogger(__name__)


def _correlation(request: Request) -> str:
    return correlation_for_request(request) or get_correlation_id() or new_ulid()


def _field_from_loc(loc: tuple[Any, ...]) -> str:
    parts = [str(part) for part in loc if part not in {"body", "query", "path", "header"}]
    return ".".join(parts) if parts else "request"


def _validation_details(exc: RequestValidationError) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    for error in exc.errors():
        details.append(
            {
                "field": _field_from_loc(tuple(error.get("loc", ()))),
                "issue": str(error.get("msg", "invalid value")),
            }
        )
    return details


def _is_unsupported_event_type(exc: RequestValidationError) -> bool:
    return any(
        "event_type" in tuple(error.get("loc", ()))
        and (error.get("type") == "enum" or "enum" in str(error.get("msg", "")).lower())
        for error in exc.errors()
    )


def _is_json_decode_error(exc: RequestValidationError) -> bool:
    return any(error.get("type") == "json_invalid" for error in exc.errors())


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers for expected and unexpected failures."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                correlation_id=_correlation(request),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        if _is_json_decode_error(exc):
            code = "malformed_request"
            message = "Request body is not valid JSON"
            status_code = 400
        elif _is_unsupported_event_type(exc):
            code = "unsupported_event_type"
            message = "event_type is outside the v1 scope"
            status_code = 422
        else:
            code = "validation_error"
            message = "Request validation failed"
            status_code = 422
        return JSONResponse(
            status_code=status_code,
            content=error_payload(
                code=code,
                message=message,
                details=_validation_details(exc),
                correlation_id=_correlation(request),
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        if exc.status_code == 404:
            code = "not_found"
            message = "Resource not found"
        elif exc.status_code == 405:
            code = "method_not_allowed"
            message = "Method not allowed"
        else:
            code = "malformed_request"
            message = str(exc.detail) if exc.detail else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=code,
                message=message,
                details=[],
                correlation_id=_correlation(request),
            ),
        )

    @app.exception_handler(DBAPIError)
    async def handle_dbapi_error(request: Request, exc: DBAPIError) -> JSONResponse:
        logger.warning(
            "database dependency failure",
            extra={"event": "dependency_unavailable", "path": request.url.path},
        )
        return JSONResponse(
            status_code=503,
            content=error_payload(
                code="dependency_unavailable",
                message="Database is unavailable",
                details=[],
                correlation_id=_correlation(request),
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy_error(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.exception("database error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content=error_payload(
                code="internal_error",
                message="An internal database error occurred",
                details=[],
                correlation_id=_correlation(request),
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled exception", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content=error_payload(
                code="internal_error",
                message="An internal error occurred",
                details=[],
                correlation_id=_correlation(request),
            ),
        )
