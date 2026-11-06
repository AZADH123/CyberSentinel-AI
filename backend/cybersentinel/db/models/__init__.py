"""ORM model registry.

Importing this module registers every model with ``Base.metadata``. Alembic and tests must
import this module rather than individual model files.
"""

from __future__ import annotations

from cybersentinel.db.models.alert import Alert
from cybersentinel.db.models.audit import AuditLog
from cybersentinel.db.models.event import Event
from cybersentinel.db.models.evidence import Evidence
from cybersentinel.db.models.incident import Incident
from cybersentinel.db.models.investigation import Investigation
from cybersentinel.db.models.report import Report
from cybersentinel.db.models.review import Review

__all__ = [
    "Alert",
    "AuditLog",
    "Event",
    "Evidence",
    "Incident",
    "Investigation",
    "Report",
    "Review",
]
