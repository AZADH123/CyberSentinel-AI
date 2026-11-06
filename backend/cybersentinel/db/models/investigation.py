"""Investigation execution record."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersentinel.db.base import Base
from cybersentinel.utils.time import utc_now

if TYPE_CHECKING:
    from cybersentinel.db.models.incident import Incident
    from cybersentinel.db.models.report import Report


class Investigation(Base):
    """One execution of the graph for an incident, with persisted state for recovery."""

    __tablename__ = "investigations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','completed','completed_degraded','failed',"
            "'cancelled','interrupted')",
            name="status_allowed",
        ),
        Index("ix_investigations_incident_created", "incident_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey(
            "incidents.id", ondelete="CASCADE", name="fk_investigations_incident_id_incidents"
        ),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    graph_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    risk_model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    incident: Mapped[Incident] = relationship()
    reports: Mapped[list[Report]] = relationship(back_populates="investigation")
