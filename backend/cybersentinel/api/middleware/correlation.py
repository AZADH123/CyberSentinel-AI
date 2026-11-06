"""Request correlation, structured access logging and response header injection."""

from __future__ import annotations

import logging
import time

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from cybersentinel.core.logging import clear_correlation_id, set_correlation_id
from cybersentinel.utils.ids import new_ulid

logger = logging.getLogger("cybersentinel.access")


def correlation_for_request(request: Request) -> str | None:
    """Return the correlation ID attached to an ASGI request scope."""
    value = getattr(request.state, "correlation_id", None)
    return str(value) if value else None


class CorrelationIdMiddleware:
    """Generate one ULID per request and attach it to logs and responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = new_ulid()
        set_correlation_id(correlation_id)
        scope.setdefault("state", {})
        scope["state"]["correlation_id"] = correlation_id

        started = time.perf_counter()
        status_code = 500

        async def send_with_header(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                headers = list(message.get("headers", []))
                if not any(name.lower() == b"x-correlation-id" for name, _ in headers):
                    headers.append((b"x-correlation-id", correlation_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.info(
                "request completed",
                extra={
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            clear_correlation_id()
