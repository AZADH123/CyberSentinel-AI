"""FastAPI application factory.

The app is assembled explicitly so tests can inject a test database and settings without
mutating module globals. Schema creation is never performed here; Alembic owns migrations.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from cybersentinel.api.errors import register_exception_handlers
from cybersentinel.api.middleware.correlation import CorrelationIdMiddleware
from cybersentinel.api.middleware.limits import BodySizeLimitMiddleware
from cybersentinel.api.middleware.rate_limit import RateLimitMiddleware
from cybersentinel.api.routers import alerts, health, incidents, investigations, reviews
from cybersentinel.core.config import Settings, get_settings
from cybersentinel.core.constants import API_PREFIX, APP_NAME
from cybersentinel.core.logging import configure_logging
from cybersentinel.db.session import Database


def create_app(
    settings: Settings | None = None,
    database: Database | None = None,
) -> FastAPI:
    """Build the API application.

    Args:
        settings: Optional validated settings (tests inject an isolated instance).
        database: Optional database manager (tests inject a test database).
    """
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level, resolved_settings.log_json)
    resolved_database = database or Database(
        resolved_settings.database_url, echo=resolved_settings.database_echo
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await app.state.db.dispose()

    app = FastAPI(
        title=APP_NAME,
        version=resolved_settings.app_version,
        description=(
            "Evidence-grounded SOC alert triage prototype. Recommend-only: no containment "
            "or remediation tools exist."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )
    app.state.settings = resolved_settings
    app.state.db = resolved_database

    # Added first means innermost. Correlation is outermost so every response and error,
    # including middleware rejections, carries one ID.
    app.add_middleware(
        RateLimitMiddleware, limit_per_minute=resolved_settings.rate_limit_per_minute
    )
    app.add_middleware(
        BodySizeLimitMiddleware, max_bytes=resolved_settings.max_request_bytes
    )
    app.add_middleware(CorrelationIdMiddleware)

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(alerts.router, prefix=API_PREFIX)
    app.include_router(incidents.router, prefix=API_PREFIX)
    app.include_router(investigations.router, prefix=API_PREFIX)
    app.include_router(reviews.router, prefix=API_PREFIX)
    return app


app = create_app()
