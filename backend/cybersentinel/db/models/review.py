"""Immutable review records."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cybersentinel.db.base import Base
from cybersentinel.utils.time import utc_now

if TYPE_CHECKING:
    from cybersentinel.db.models.incident import Incident


class Review(Base):
    """One review decision for an incident."""

    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint(
            "disposition IN ('accept','reject','escalate')", name="disposition_allowed"
        ),
        Index("ix_reviews_incident_reviewed_at", "incident_id", "reviewed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    incident_id: Mapped[str] = mapped_column(
        String(16),
        ForeignKey("incidents.id", ondelete="CASCADE", name="fk_reviews_incident_id_incidents"),
        nullable=False,
    )
    reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    disposition: Mapped[str] = mapped_column(String(16), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    incident: Mapped[Incident] = relationship(back_populates="reviews")
