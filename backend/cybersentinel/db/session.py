"""Async database engine and session factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class Database:
    """Own the application's async engine and session factory."""

    def __init__(
        self,
        url: str,
        *,
        echo: bool = False,
        engine_kwargs: dict[str, Any] | None = None,
    ) -> None:
        if not url.startswith("postgresql+asyncpg://"):
            raise ValueError("CyberSentinel requires a PostgreSQL 16 asyncpg URL")
        self.url = url
        self.engine: AsyncEngine = create_async_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            **({"connect_args": {"timeout": 5}} if engine_kwargs is None else engine_kwargs),
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield a session and guarantee rollback on an unexpected exception."""
        session = self.session_factory()
        try:
            yield session
            if session.in_transaction():
                await session.commit()
        except BaseException:
            if session.in_transaction():
                await session.rollback()
            raise
        finally:
            await session.close()

    async def ping(self) -> float:
        """Return database round-trip latency in milliseconds, raising on failure."""
        import time

        started = time.perf_counter()
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return round((time.perf_counter() - started) * 1000, 2)

    async def dispose(self) -> None:
        """Dispose the connection pool."""
        await self.engine.dispose()

    async def table_names(self) -> set[str]:
        """Return user table names (used by diagnostics and tests)."""
        async with self.engine.connect() as connection:
            result = await connection.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            return {row[0] for row in result}
