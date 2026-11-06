"""Append-only evidence record."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy import event as sa_event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from cybersentinel.db.base import Base
from cybersentinel.utils.time import utc_now


class Evidence(Base):
    """An immutable, checksummed fact a report is allowed to cite."""

    __tablename__ = "evidence"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('alert_field','correlated_event','enrichment','rule_finding',"
            "'attack_mapping','derived')",
            name="kind_allowed",
        ),
        Index("ix_evidence_investigation_captured", "investigation_id", "captured_at"),
        Index("uq_evidence_investigation_key", "investigation_id", "evidence_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    investigation_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey(
            "investigations.id",
            ondelete="CASCADE",
            name="fk_evidence_investigation_id_investigations",
        ),
        nullable=False,
    )
    evidence_key: Mapped[str] = mapped_column(String(8), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    reference: Mapped[str] = mapped_column(String(128), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    supersedes: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence.id", ondelete="RESTRICT", name="fk_evidence_supersedes_evidence"),
        nullable=True,
    )


def _reject_mutation(*_: object) -> None:
    raise ValueError("evidence is append-only; insert a new record with supersedes")


sa_event.listen(Evidence, "before_update", _reject_mutation)
sa_event.listen(Evidence, "before_delete", _reject_mutation)
