"""Analyst-facing incident ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersentinel.db.base import Base
from cybersentinel.utils.time import utc_now

if TYPE_CHECKING:
    from cybersentinel.db.models.alert import Alert
    from cybersentinel.db.models.investigation import Investigation
    from cybersentinel.db.models.review import Review


class Incident(Base):
    """The single unit of work opened from an alert."""

    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','investigating','awaiting_review','accepted',"
            "'rejected','escalated','failed')",
            name="status_allowed",
        ),
        CheckConstraint(
            "severity IN ('informational','low','medium','high')", name="severity_allowed"
        ),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="risk_score_range"),
        CheckConstraint(
            "risk_band IN ('informational','low','medium','high')", name="risk_band_allowed"
        ),
        CheckConstraint("confidence IN ('low','medium','high')", name="confidence_allowed"),
        Index("ix_incidents_queue", "status", "risk_score", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    alert_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("alerts.id", ondelete="RESTRICT", name="fk_incidents_alert_id_alerts"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default="informational"
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_band: Mapped[str] = mapped_column(
        String(16), nullable=False, default="informational"
    )
    confidence: Mapped[str] = mapped_column(String(16), nullable=False, default="low")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    alert: Mapped[Alert] = relationship(back_populates="incident")
    investigations: Mapped[list[Investigation]] = relationship(back_populates="incident")
    reviews: Mapped[list[Review]] = relationship(back_populates="incident")
