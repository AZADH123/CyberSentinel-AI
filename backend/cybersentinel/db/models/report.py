"""Immutable investigation report rows."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersentinel.db.base import Base
from cybersentinel.utils.time import utc_now

if TYPE_CHECKING:
    from cybersentinel.db.models.investigation import Investigation


class Report(Base):
    """One versioned, immutable report for an investigation."""

    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint(
            "investigation_id", "version", name="uq_reports_investigation_version"
        ),
        Index("ix_reports_investigation_id", "investigation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    investigation_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "investigations.id",
            ondelete="CASCADE",
            name="fk_reports_investigation_id_investigations",
        ),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="report-v1")
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    degraded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_by: Mapped[str] = mapped_column(
        String(64), nullable=False, default="deterministic"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    investigation: Mapped[Investigation] = relationship(back_populates="reports")
