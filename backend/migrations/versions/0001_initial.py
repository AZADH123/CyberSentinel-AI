"""Initial foundation schema: alerts, events, incidents and audit logs.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_event", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalized_event", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("dedupe_hash", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("duplicate_of", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "event_type IN ('authentication', 'authorization', 'account_change')",
            name="ck_alerts_event_type_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["duplicate_of"],
            ["alerts.id"],
            name="fk_alerts_duplicate_of_alerts",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_alerts"),
        sa.UniqueConstraint("idempotency_key", name="uq_alerts_idempotency_key"),
    )
    op.create_index("ix_alerts_dedupe_hash", "alerts", ["dedupe_hash"], unique=False)
    op.create_index("ix_alerts_event_time", "alerts", ["event_time"], unique=False)

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("host", sa.String(length=253), nullable=False),
        sa.Column("source_ip", sa.String(length=45), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("asset_criticality", sa.String(length=16), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "failure_count >= 0 AND failure_count <= 10000",
            name="ck_events_failure_count_range",
        ),
        sa.CheckConstraint(
            "outcome IN ('success', 'failure', 'unknown')",
            name="ck_events_outcome_allowed",
        ),
        sa.CheckConstraint(
            "asset_criticality IN ('low', 'medium', 'high', 'critical')",
            name="ck_events_asset_criticality_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            name="fk_events_alert_id_alerts",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_events"),
        sa.UniqueConstraint("alert_id", name="uq_events_alert_id"),
    )
    op.create_index(
        "ix_events_username_event_time",
        "events",
        ["username", "event_time"],
        unique=False,
    )
    op.create_index(
        "ix_events_source_ip_event_time",
        "events",
        ["source_ip", "event_time"],
        unique=False,
    )
    op.create_index(
        "ix_events_host_event_time",
        "events",
        ["host", "event_time"],
        unique=False,
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column(
            "severity", sa.String(length=16), nullable=False, server_default="informational"
        ),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "risk_band",
            sa.String(length=16),
            nullable=False,
            server_default="informational",
        ),
        sa.Column("confidence", sa.String(length=16), nullable=False, server_default="low"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('open','investigating','awaiting_review','accepted',"
            "'rejected','escalated','failed')",
            name="ck_incidents_status_allowed",
        ),
        sa.CheckConstraint(
            "severity IN ('informational','low','medium','high')",
            name="ck_incidents_severity_allowed",
        ),
        sa.CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="ck_incidents_risk_score_range",
        ),
        sa.CheckConstraint(
            "risk_band IN ('informational','low','medium','high')",
            name="ck_incidents_risk_band_allowed",
        ),
        sa.CheckConstraint(
            "confidence IN ('low','medium','high')",
            name="ck_incidents_confidence_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            name="fk_incidents_alert_id_alerts",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_incidents"),
        sa.UniqueConstraint("alert_id", name="uq_incidents_alert_id"),
    )
    op.create_index(
        "ix_incidents_queue",
        "incidents",
        ["status", "risk_score", "created_at"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(length=16), nullable=False, server_default="success"),
        sa.Column("correlation_id", sa.String(length=26), nullable=False),
        sa.Column(
            "detail",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"], unique=False)
    op.create_index(
        "ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"], unique=False
    )
    op.create_index(
        "ix_audit_logs_correlation_id",
        "audit_logs",
        ["correlation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_logs_correlation_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_timestamp", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_incidents_queue", table_name="incidents")
    op.drop_table("incidents")
    op.drop_index("ix_events_host_event_time", table_name="events")
    op.drop_index("ix_events_source_ip_event_time", table_name="events")
    op.drop_index("ix_events_username_event_time", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_alerts_event_time", table_name="alerts")
    op.drop_index("ix_alerts_dedupe_hash", table_name="alerts")
    op.drop_table("alerts")
