"""Settings validation tests (no network or database required)."""

from __future__ import annotations

import pytest
from cybersentinel.core.config import Settings
from pydantic import ValidationError


def test_default_settings_require_postgresql() -> None:
    settings = Settings(_env_file=None, app_env="test")
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_sqlite_url_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="sqlite+aiosqlite:///./app.db")


def test_live_enrichment_requires_key() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            enrichment_mode="live",
            virustotal_api_key=None,
        )


def test_llm_enabled_requires_key() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, llm_enabled=True, gemini_api_key=None)


def test_mock_mode_works_without_keys() -> None:
    settings = Settings(
        _env_file=None,
        enrichment_mode="mock",
        llm_enabled=False,
    )
    assert settings.enrichment_mode == "mock"
    assert not settings.virustotal_configured


def test_database_url_driver_normalisation() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql://user:pass@localhost:5432/db",
    )
    assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"
