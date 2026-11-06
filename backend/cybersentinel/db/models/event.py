"""Normalised event ORM model: the queryable correlation substrate."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersentinel.db.base import Base
from cybersentinel.utils.time import utc_now

if TYPE_CHECKING:
    from cybersentinel.db.models.alert import Alert


class Event(Base):
    """One normalised authentication event linked one-to-one to an alert."""

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "failure_count >= 0 AND failure_count <= 10000", name="failure_count_range"
        ),
        CheckConstraint(
            "outcome IN ('success', 'failure', 'unknown')", name="outcome_allowed"
        ),
        CheckConstraint(
            "asset_criticality IN ('low', 'medium', 'high', 'critical')",
            name="asset_criticality_allowed",
        ),
        Index("ix_events_username_event_time", "username", "event_time"),
        Index("ix_events_source_ip_event_time", "source_ip", "event_time"),
        Index("ix_events_host_event_time", "host", "event_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE", name="fk_events_alert_id_alerts"),
        nullable=False,
        unique=True,
    )
    username: Mapped[str] = mapped_column(String(128), nullable=False)
    host: Mapped[str] = mapped_column(String(253), nullable=False)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asset_criticality: Mapped[str] = mapped_column(String(16), nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    alert: Mapped[Alert] = relationship(back_populates="event")
