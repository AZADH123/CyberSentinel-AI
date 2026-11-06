"""Application settings loaded from the environment.

All runtime configuration is validated once at startup. Secrets use ``SecretStr`` so they do
not leak through reprs or structured logs. Mock/offline defaults keep the application usable
without paid provider credentials.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from cybersentinel.core.constants import (
    CORRELATION_MAX_EVENTS,
    CORRELATION_WINDOW_MINUTES,
    MAX_REQUEST_BYTES,
    PLACEHOLDER_SECRET_MARKERS,
    RISK_MODEL_VERSION,
)


def _is_usable_secret(value: SecretStr | None) -> bool:
    """Return whether a non-placeholder provider credential is present."""
    if value is None:
        return False
    raw = value.get_secret_value().strip()
    if len(raw) < 16:
        return False
    lowered = raw.lower()
    return not any(marker in lowered for marker in PLACEHOLDER_SECRET_MARKERS)


class Settings(BaseSettings):
    """Validated process configuration.

    PostgreSQL 16 is the only supported database. The default points at the local Compose
    database; deployment overrides it with the same variable.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = True

    database_url: str = (
        "postgresql+asyncpg://cybersentinel:change-me-local@127.0.0.1:55432/cybersentinel"
    )
    database_echo: bool = False

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash"
    virustotal_api_key: SecretStr | None = None

    enrichment_mode: Literal["live", "mock", "off"] = "mock"
    enrichment_timeout_s: float = Field(default=5.0, gt=0, le=60)
    enrichment_daily_budget: int = Field(default=200, ge=0, le=100_000)
    enrichment_cache_ttl_h: int = Field(default=24, ge=1, le=720)

    llm_enabled: bool = False
    llm_timeout_s: float = Field(default=20.0, gt=0, le=120)

    correlation_window_minutes: int = Field(default=CORRELATION_WINDOW_MINUTES, ge=1, le=1440)
    correlation_max_events: int = Field(default=CORRELATION_MAX_EVENTS, ge=1, le=1000)
    risk_model_version: str = RISK_MODEL_VERSION

    max_request_bytes: int = Field(default=MAX_REQUEST_BYTES, ge=1024, le=16 * 1024 * 1024)
    rate_limit_per_minute: int = Field(default=60, ge=0, le=100_000)
    max_event_age_days: int = Field(default=90, ge=1, le=3650)
    reviewer_name: str = Field(default="local-reviewer", min_length=1, max_length=128)

    @field_validator("database_url")
    @classmethod
    def normalise_database_url(cls, value: str) -> str:
        """Accept conventional PostgreSQL URLs and select the asyncpg driver."""
        url = value.strip()
        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url.removeprefix("postgres://")
        if url.startswith("sqlite"):
            raise ValueError("SQLite is not supported; DATABASE_URL must be PostgreSQL 16")
        if not url.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use the postgresql+asyncpg:// driver")
        return url

    @field_validator("log_level", mode="before")
    @classmethod
    def normalise_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_provider_configuration(self) -> Settings:
        """Fail closed when a live provider is enabled without a usable credential."""
        if self.enrichment_mode == "live" and not _is_usable_secret(self.virustotal_api_key):
            raise ValueError(
                "ENRICHMENT_MODE=live requires a non-placeholder VIRUSTOTAL_API_KEY"
            )
        if self.llm_enabled and not _is_usable_secret(self.gemini_api_key):
            raise ValueError("LLM_ENABLED=true requires a non-placeholder GEMINI_API_KEY")
        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL 16 async URL")
        return self

    @property
    def virustotal_configured(self) -> bool:
        """Whether a usable VirusTotal credential is present (never exposes the value)."""
        return _is_usable_secret(self.virustotal_api_key)

    @property
    def gemini_configured(self) -> bool:
        """Whether a usable Gemini credential is present (never exposes the value)."""
        return _is_usable_secret(self.gemini_api_key)

    @property
    def sync_database_url(self) -> str:
        """Synchronous URL for diagnostics; not used by the async application."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide validated settings instance."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings (used by tests and explicit reload operations)."""
    get_settings.cache_clear()
