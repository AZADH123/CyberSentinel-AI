"""Add evidence, investigations, reports and reviews tables.

Revision ID: 0002_add_reports_reviews
Revises: 0001_initial
Create Date: 2026-11-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_add_reports_reviews"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(length=12), nullable=False),
        sa.Column("incident_id", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("graph_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("risk_model_version", sa.String(length=32), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("prompt_version", sa.String(length=32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','completed','completed_degraded','failed','cancelled','interrupted')",
            name="ck_investigations_status_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name="fk_investigations_incident_id_incidents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_investigations"),
    )
    op.create_index(
        "ix_investigations_incident_created",
        "investigations",
        ["incident_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("investigation_id", sa.String(length=12), nullable=False),
        sa.Column("evidence_key", sa.String(length=8), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column("reference", sa.String(length=128), nullable=False),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("supersedes", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "kind IN ('alert_field','correlated_event','enrichment','rule_finding','attack_mapping','derived')",
            name="ck_evidence_kind_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["investigations.id"],
            name="fk_evidence_investigation_id_investigations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes"],
            ["evidence.id"],
            name="fk_evidence_supersedes_evidence",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_evidence"),
        sa.UniqueConstraint("investigation_id", "evidence_key", name="uq_evidence_investigation_key"),
    )
    op.create_index(
        "ix_evidence_investigation_captured",
        "evidence",
        ["investigation_id", "captured_at"],
        unique=False,
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("investigation_id", sa.String(length=12), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("schema_version", sa.String(length=32), nullable=False, server_default="report-v1"),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("degraded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("generated_by", sa.String(length=64), nullable=False, server_default="deterministic"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["investigations.id"],
            name="fk_reports_investigation_id_investigations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reports"),
        sa.UniqueConstraint("investigation_id", "version", name="uq_reports_investigation_version"),
    )
    op.create_index("ix_reports_investigation_id", "reports", ["investigation_id"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", sa.String(length=16), nullable=False),
        sa.Column("reviewer", sa.String(length=128), nullable=False),
        sa.Column("disposition", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "disposition IN ('accept','reject','escalate')",
            name="ck_reviews_disposition_allowed",
        ),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
            name="fk_reviews_incident_id_incidents",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reviews"),
    )
    op.create_index(
        "ix_reviews_incident_reviewed_at", "reviews", ["incident_id", "reviewed_at"], unique=False
    )


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("reports")
    op.drop_table("evidence")
    op.drop_table("investigations")
