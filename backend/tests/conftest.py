"""Shared test fixtures.

Tests run against a real PostgreSQL 16 database. Alembic applies the schema once per session;
each test starts from truncated application tables. The application dependency graph is
constructed exactly as in production, with only settings overridden.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from datetime import timedelta

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from cybersentinel.api.main import create_app
from cybersentinel.core.config import Settings
from cybersentinel.db.session import Database
from cybersentinel.utils.time import utc_now
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://cybersentinel:change-me-local@127.0.0.1:55432/cybersentinel_test",
)


@pytest.fixture(scope="session")
def migrated_database() -> Iterator[None]:
    """Apply Alembic migrations to the dedicated test database once per session."""
    config = Config(os.path.join(BACKEND_ROOT, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(BACKEND_ROOT, "migrations"))
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    try:
        command.upgrade(config, "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
    yield


@pytest_asyncio.fixture
async def clean_database(migrated_database: None) -> AsyncIterator[None]:
    """Truncate application tables before every test, preserving the migration version."""
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "TRUNCATE TABLE audit_logs, incidents, events, alerts "
                "RESTART IDENTITY CASCADE"
            )
        )
    await engine.dispose()
    yield


@pytest.fixture
def settings() -> Settings:
    """Isolated test settings: PostgreSQL, mock enrichment, no LLM, no throttling."""
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=TEST_DATABASE_URL,
        log_json=False,
        llm_enabled=False,
        enrichment_mode="mock",
        rate_limit_per_minute=100_000,
        max_request_bytes=262_144,
    )


@pytest_asyncio.fixture
async def app(settings: Settings) -> AsyncIterator[object]:
    """Application instance with a disposable PostgreSQL engine."""
    database = Database(TEST_DATABASE_URL)
    application = create_app(settings=settings, database=database)
    yield application
    await database.dispose()


@pytest_asyncio.fixture
async def client(app: object) -> AsyncIterator[AsyncClient]:
    """HTTPX client bound to the ASGI app without opening a network socket."""
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(
        transport=transport,
        base_url="http://cybersentinel.test",
        headers={"Content-Type": "application/json"},
    ) as http_client:
        yield http_client


@pytest_asyncio.fixture
async def db_session(app: object) -> AsyncIterator[AsyncSession]:
    """Read-only convenience session for assertions against persisted rows."""
    database: Database = app.state.db  # type: ignore[attr-defined]
    async with database.session() as session:
        yield session


def alert_payload(**overrides: object) -> dict[str, object]:
    """Build a valid synthetic alert within the ingestion age window."""
    event_time = (utc_now() - timedelta(minutes=1)).replace(microsecond=0)
    payload: dict[str, object] = {
        "source": "lab-auth-simulator",
        "event_type": "authentication",
        "event_time": event_time.isoformat().replace("+00:00", "Z"),
        "username": "admin",
        "source_ip": "198.51.100.24",
        "host": "vpn-01",
        "outcome": "failure",
        "failure_count": 18,
        "asset_criticality": "high",
        "raw_event": {"message": "Repeated login failures"},
    }
    payload.update(overrides)
    return payload
