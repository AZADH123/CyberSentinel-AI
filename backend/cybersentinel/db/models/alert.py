"""Alert ORM model: the immutable record of exactly what was received."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersentinel.core.constants import VALID_EVENT_TYPES
from cybersentinel.db.base import Base
from cybersentinel.utils.ids import new_uuid7
from cybersentinel.utils.time import utc_now

if TYPE_CHECKING:
    from cybersentinel.db.models.event import Event
    from cybersentinel.db.models.incident import Incident


class Alert(Base):
    """A raw security alert exactly as received, plus a canonical normalised view."""

    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('authentication', 'authorization', 'account_change')",
            name="event_type_allowed",
        ),
        Index("ix_alerts_dedupe_hash", "dedupe_hash"),
        Index("ix_alerts_event_time", "event_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=new_uuid7
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_event: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    normalized_event: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    dedupe_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    duplicate_of: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("alerts.id", ondelete="RESTRICT", name="fk_alerts_duplicate_of_alerts"),
        nullable=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    event: Mapped[Event] = relationship(back_populates="alert", uselist=False)
    incident: Mapped[Incident | None] = relationship(back_populates="alert", uselist=False)
    duplicate_of_alert: Mapped[Alert | None] = relationship(
        remote_side="Alert.id", back_populates="duplicates"
    )
    duplicates: Mapped[list[Alert]] = relationship(back_populates="duplicate_of_alert")

    @property
    def valid_event_types(self) -> frozenset[str]:
        """Expose the allowlist for documentation/tests without duplicating it."""
        return VALID_EVENT_TYPES
