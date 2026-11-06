"""Request body-size enforcement.

The check happens before Pydantic parses the body and also while streaming, so a client that
omits Content-Length cannot bypass the configured limit.
"""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from cybersentinel.schemas.error import error_payload
from cybersentinel.utils.ids import new_ulid


class _BodyTooLarge(Exception):
    pass


def _correlation_id(scope: Scope) -> str:
    state = scope.get("state") or {}
    return str(state.get("correlation_id") or new_ulid())


async def send_error(
    scope: Scope,
    send: Send,
    *,
    status_code: int,
    code: str,
    message: str,
) -> None:
    """Send a complete JSON error response from ASGI middleware."""
    body = json.dumps(
        error_payload(
            code=code,
            message=message,
            details=[],
            correlation_id=_correlation_id(scope),
        )
    ).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                (b"content-type", b"application/json; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"x-correlation-id", _correlation_id(scope).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


class BodySizeLimitMiddleware:
    """Reject request bodies larger than ``max_bytes`` with 413."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {name.lower(): value for name, value in scope.get("headers", [])}
        declared = headers.get(b"content-length")
        if declared is not None:
            try:
                if int(declared) > self.max_bytes:
                    await send_error(
                        scope,
                        send,
                        status_code=413,
                        code="payload_too_large",
                        message=f"Request body exceeds {self.max_bytes} bytes",
                    )
                    return
            except ValueError:
                await send_error(
                    scope,
                    send,
                    status_code=400,
                    code="malformed_request",
                    message="Invalid Content-Length header",
                )
                return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _BodyTooLarge
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLarge:
            if not response_started:
                await send_error(
                    scope,
                    send,
                    status_code=413,
                    code="payload_too_large",
                    message=f"Request body exceeds {self.max_bytes} bytes",
                )
