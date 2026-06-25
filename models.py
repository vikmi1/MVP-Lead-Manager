from datetime import datetime
from pydantic import BaseModel, field_validator


class LeadCreate(BaseModel):
    name: str | None = None
    contact: str
    source: str | None = None
    comment: str | None = None
    consent: bool

    @field_validator("consent")
    @classmethod
    def consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("consent must be true")
        return v


class LeadOut(BaseModel):
    id: int
    created_at: datetime
    name: str | None
    contact: str
    source: str | None
    comment: str | None
    consent: bool
