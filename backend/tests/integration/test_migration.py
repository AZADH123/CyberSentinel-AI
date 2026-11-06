"""Alembic migration contract tests (M1 gate)."""

from __future__ import annotations

from cybersentinel.db.session import Database
from sqlalchemy import text

from tests.conftest import TEST_DATABASE_URL


async def test_initial_migration_applied_cleanly() -> None:
    database = Database(TEST_DATABASE_URL)
    try:
        tables = await database.table_names()
        assert {
            "alerts",
            "events",
            "incidents",
            "audit_logs",
            "alembic_version",
            "investigations",
            "evidence",
            "reports",
            "reviews",
        } <= tables

        async with database.engine.connect() as connection:
            version = (
                await connection.execute(
                    text("SELECT version_num FROM alembic_version")
                )
            ).scalar_one()
        assert version == "0002_add_reports_reviews"
    finally:
        await database.dispose()
