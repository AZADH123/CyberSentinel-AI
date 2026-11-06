"""Repository registry."""

from __future__ import annotations

from cybersentinel.db.repositories.alerts import AlertRepository
from cybersentinel.db.repositories.incidents import IncidentRepository
from cybersentinel.db.repositories.investigations import InvestigationRepository

__all__ = ["AlertRepository", "IncidentRepository", "InvestigationRepository"]
