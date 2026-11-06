"""FastAPI dependency providers.

Dependencies read from ``app.state`` rather than module-level globals, which keeps the app
factory testable and avoids a second configuration source.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from cybersentinel.core.config import Settings
from cybersentinel.db.session import Database


def get_settings_dep(request: Request) -> Settings:
    """Return the validated settings bound to this application instance."""
    settings: Settings = request.app.state.settings
    return settings


def get_database(request: Request) -> Database:
    """Return the application database manager."""
    database: Database = request.app.state.db
    return database


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped async session with rollback on failure."""
    database: Database = request.app.state.db
    async with database.session() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
DatabaseDep = Annotated[Database, Depends(get_database)]
