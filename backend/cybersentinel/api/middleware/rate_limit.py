"""In-process rate limiting for the localhost prototype.

The limit is per API process, not a distributed guarantee. That is adequate for the
single-worker v1 and is documented as a limitation; Redis is deliberately not introduced.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from cybersentinel.api.middleware.limits import send_error


class RateLimitMiddleware:
    """Sliding-window request throttle with standard rate-limit headers."""

    def __init__(self, app: ASGIApp, *, limit_per_minute: int) -> None:
        self.app = app
        self.limit = limit_per_minute
        self.window_seconds = 60.0
        self._events: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or self.limit <= 0:
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", ""))
        if path == "/health":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        key = str(client[0]) if client else "unknown"
        now = time.monotonic()
        events = self._events[key]
        while events and now - events[0] >= self.window_seconds:
            events.popleft()

        reset_seconds = max(1, math.ceil(self.window_seconds - (now - events[0]))) if events else 60
        if len(events) >= self.limit:
            await send_error(
                scope,
                send,
                status_code=429,
                code="rate_limited",
                message=f"Rate limit of {self.limit} requests per minute exceeded",
            )
            return

        events.append(now)
        remaining = max(0, self.limit - len(events))
        reset_epoch = int(time.time()) + reset_seconds

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-ratelimit-limit", str(self.limit).encode("ascii")),
                        (b"x-ratelimit-remaining", str(remaining).encode("ascii")),
                        (b"x-ratelimit-reset", str(reset_epoch).encode("ascii")),
                    ]
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)
