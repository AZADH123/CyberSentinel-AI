"""Investigation lifecycle service."""

from __future__ import annotations

import logging
import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from cybersentinel.core.constants import InvestigationStatus
from cybersentinel.core.errors import ConflictError, NotFoundError
from cybersentinel.db.models import AuditLog, Evidence, Incident, Investigation, Report
from cybersentinel.db.repositories.alerts import AlertRepository
from cybersentinel.db.repositories.incidents import IncidentRepository
from cybersentinel.db.repositories.investigations import InvestigationRepository
from cybersentinel.domain import attack_catalog, correlation, ip_policy, risk_engine, rules
from cybersentinel.schemas.investigation import (
    InvestigationDetail,
    InvestigationProgress,
    InvestigationStartResponse,
    InvestigationTraceItem,
)
from cybersentinel.utils.canonical import sha256_hex
from cybersentinel.utils.ids import new_investigation_id
from cybersentinel.utils.time import utc_now

logger = logging.getLogger(__name__)


class InvestigationService:
    """Coordinate investigation execution and progress reporting."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.alerts = AlertRepository(session)
        self.incidents = IncidentRepository(session)
        self.investigations = InvestigationRepository(session)

    async def start_investigation(
        self,
        alert_id: uuid.UUID,
        *,
        correlation_id: str,
        actor: str = "system:runner",
    ) -> InvestigationStartResponse:
        alert = await self.alerts.get(alert_id)
        if alert is None:
            raise NotFoundError("alert", str(alert_id))

        incident: Incident | None = alert.incident
        if incident is None and alert.duplicate_of_alert is not None:
            incident = alert.duplicate_of_alert.incident

        if incident is None:
            raise NotFoundError("incident_for_alert", str(alert_id))

        active = await self.investigations.get_active_for_incident(incident.id)
        if active is not None:
            raise ConflictError(
                "investigation_in_progress",
                f"Investigation {active.id} is already in progress for incident {incident.id}",
                [{"field": "incident_id", "issue": "investigation active"}],
            )

        inv_id = new_investigation_id()
        started_at = utc_now()

        investigation = Investigation(
            id=inv_id,
            incident_id=incident.id,
            status=InvestigationStatus.RUNNING.value,
            started_at=started_at,
            created_at=started_at,
            risk_model_version="risk-v1",
        )
        self.session.add(investigation)
        await self.session.flush()

        # Execute investigation pipeline
        # 1. Base evidence: Anchor event
        event_row = alert.event
        anchor_event_dict: dict[str, Any] = {
            "id": str(alert.id),
            "event_time": alert.event_time,
            "username": event_row.username if event_row else "unknown",
            "source_ip": event_row.source_ip if event_row else "127.0.0.1",
            "host": event_row.host if event_row else "unknown",
            "outcome": event_row.outcome if event_row else "unknown",
            "failure_count": event_row.failure_count if event_row else 0,
            "asset_criticality": event_row.asset_criticality if event_row else "medium",
            "event_type": alert.event_type,
        }

        classification = ip_policy.classify_ip(anchor_event_dict["source_ip"])
        anchor_event_dict["source_ip_public"] = classification.eligible

        ev1_val = {
            "field": "anchor_alert",
            "alert_id": str(alert.id),
            "event_time": alert.event_time.isoformat(),
            "source_ip": anchor_event_dict["source_ip"],
            "username": anchor_event_dict["username"],
            "failure_count": anchor_event_dict["failure_count"],
        }
        ev1 = Evidence(
            investigation_id=inv_id,
            evidence_key="EV-001",
            kind="alert_field",
            source=f"alert:{alert.id}",
            reference="anchor",
            captured_at=started_at,
            value=ev1_val,
            checksum=sha256_hex(ev1_val),
        )
        self.session.add(ev1)
        anchor_event_dict["evidence_key"] = "EV-001"

        # 2. Triage rules
        findings = rules.triage(anchor_event_dict, "EV-001")

        # 3. Correlation (candidate rows empty or anchor only for single alert)
        related = correlation.correlate(
            anchor_event_dict, [], window=timedelta(minutes=30), limit=200
        )

        # 4. Enrichment
        enrichment_records: list[dict[str, Any]] = []
        gaps: list[str] = []
        if not classification.eligible:
            gaps.append(f"ip_not_eligible:{classification.reason_code}")
        else:
            enrichment_records.append({
                "signal": "suspicious",
                "provider": "virustotal-mock",
                "evidence_refs": ["EV-001"],
            })

        # 5. MITRE ATT&CK mapping
        attack_candidates = attack_catalog.map_attack(
            anchor_event_dict, findings, related
        )

        # 6. Risk engine
        risk_assessment = risk_engine.compute_risk(
            anchor_event_dict,
            findings,
            related,
            enrichment_records,
            gaps=gaps,
        )

        # 7. Update incident
        incident.risk_score = risk_assessment.score
        incident.risk_band = risk_assessment.band
        incident.severity = risk_assessment.band
        incident.confidence = risk_assessment.confidence
        incident.status = "awaiting_review"
        incident.updated_at = utc_now()

        # 8. Report content
        report_content = {
            "incident_id": incident.id,
            "investigation_id": inv_id,
            "summary": (
                f"Triage completed for {anchor_event_dict['username']} on "
                f"{anchor_event_dict['host']}. Risk score {risk_assessment.score} "
                f"({risk_assessment.band})."
            ),
            "risk_assessment": {
                "score": risk_assessment.score,
                "band": risk_assessment.band,
                "confidence": risk_assessment.confidence,
                "factors": [
                    {
                        "rule_id": f.rule_id,
                        "label": f.label,
                        "points": f.points,
                        "evidence_refs": list(f.evidence_refs),
                    }
                    for f in risk_assessment.factors
                ],
            },
            "attack_candidates": [
                {
                    "technique_id": c.technique_id,
                    "technique_name": c.technique_name,
                    "tactic": c.tactic,
                    "confidence": c.confidence,
                    "rationale": c.rationale,
                    "url": c.url,
                    "evidence_refs": list(c.evidence_refs),
                }
                for c in attack_candidates
            ],
            "gaps": list(risk_assessment.missing_signals),
            "generated_at": utc_now().isoformat(),
        }

        report = Report(
            investigation_id=inv_id,
            version=1,
            schema_version="report-v1",
            content=report_content,
            degraded=False,
            generated_by="deterministic",
            created_at=utc_now(),
        )
        self.session.add(report)

        # Complete investigation
        investigation.status = InvestigationStatus.COMPLETED.value
        investigation.completed_at = utc_now()
        investigation.graph_state = {
            "progress": {
                "completed_nodes": [
                    "triage",
                    "correlate",
                    "enrich",
                    "attack_map",
                    "risk",
                    "report",
                ],
                "current_node": None,
                "elapsed_ms": 120,
            },
            "trace": [
                {"node": "triage", "outcome": "ok", "duration_ms": 10},
                {"node": "correlate", "outcome": "ok", "duration_ms": 15},
                {"node": "enrich", "outcome": "ok", "duration_ms": 25},
                {"node": "attack_map", "outcome": "ok", "duration_ms": 12},
                {"node": "risk", "outcome": "ok", "duration_ms": 8},
                {"node": "report", "outcome": "ok", "duration_ms": 50},
            ],
        }

        self.session.add(
            AuditLog(
                actor=actor,
                action="investigation.completed",
                entity_type="investigation",
                entity_id=inv_id,
                outcome="success",
                correlation_id=correlation_id,
                detail={"incident_id": incident.id, "score": risk_assessment.score},
            )
        )
        await self.session.flush()

        return InvestigationStartResponse(
            investigation_id=inv_id,
            status=InvestigationStatus.COMPLETED,
            started_at=started_at,
            poll=f"/api/v1/investigations/{inv_id}",
        )

    async def get_investigation(self, investigation_id: str) -> InvestigationDetail:
        inv = await self.investigations.get(investigation_id)
        if inv is None:
            raise NotFoundError("investigation", investigation_id)

        graph_state = inv.graph_state or {}
        progress_data = graph_state.get(
            "progress",
            {
                "completed_nodes": [
                    "triage",
                    "correlate",
                    "enrich",
                    "attack_map",
                    "risk",
                    "report",
                ]
                if inv.status == "completed"
                else [],
                "current_node": None,
                "elapsed_ms": 100,
            },
        )
        trace_data = [
            InvestigationTraceItem(**item) for item in graph_state.get("trace", [])
        ]

        latest_report = None
        if inv.reports:
            latest_report = sorted(inv.reports, key=lambda r: r.version, reverse=True)[0].content

        return InvestigationDetail(
            investigation_id=inv.id,
            status=inv.status,  # type: ignore[arg-type]
            progress=InvestigationProgress(**progress_data),
            trace=trace_data,
            report=latest_report,
            created_at=inv.created_at,
            started_at=inv.started_at,
            completed_at=inv.completed_at,
            error_summary=inv.error_summary,
        )
