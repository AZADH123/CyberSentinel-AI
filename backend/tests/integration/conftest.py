"""Integration test fixtures: activate DB migration and table cleanup for all integration tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio


@pytest.fixture(scope="session", autouse=True)
def _require_migrated_database(migrated_database: None) -> Iterator[None]:  # noqa: PT004
    """Pull in the session-scoped migration fixture for every integration test."""
    yield


@pytest_asyncio.fixture(autouse=True)
async def _require_clean_database(clean_database: None) -> AsyncIterator[None]:  # noqa: PT004
    """Pull in the per-test table-truncation fixture for every integration test."""
    yield
