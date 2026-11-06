"""Append-only audit trail ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Uuid
from sqlalchemy import event as sa_event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from cybersentinel.db.base import Base
from cybersentinel.utils.time import utc_now


class AuditLog(Base):
    """Who did what, when, with which request correlation ID."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_correlation_id", "correlation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    outcome: Mapped[str] = mapped_column(String(16), nullable=False, default="success")
    correlation_id: Mapped[str] = mapped_column(String(26), nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


def _reject_mutation(*_: object) -> None:
    raise ValueError("audit_logs is append-only; insert a new record instead")


sa_event.listen(AuditLog, "before_update", _reject_mutation)
sa_event.listen(AuditLog, "before_delete", _reject_mutation)
