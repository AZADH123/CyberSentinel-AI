"""Review API contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cybersentinel.core.constants import Disposition, IncidentStatus


class ReviewCreate(BaseModel):
    """Payload to review an incident."""

    reviewer: str = Field(min_length=1, max_length=128)
    disposition: Disposition
    notes: str | None = Field(default=None, max_length=4096)

    @model_validator(mode="after")
    def validate_notes_requirement(self) -> ReviewCreate:
        if self.disposition in {
            Disposition.REJECT,
            Disposition.ESCALATE,
        } and (not self.notes or not self.notes.strip()):
            raise ValueError(
                f"Notes are required when disposition is '{self.disposition.value}'"
            )
        return self


class ReviewResponse(BaseModel):
    """Response returned upon successful review creation."""

    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    disposition: Disposition
    reviewer: str
    reviewed_at: datetime
    incident_status: IncidentStatus
    executed_actions: list[str] = Field(default_factory=list)
