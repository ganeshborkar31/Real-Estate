from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    badge_type: str
    icon: str | None
    color: str
    description: str | None


class TrustScoreOut(BaseModel):
    score: int
    trust_level: str


class TrustAuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    entity_id: str
    action: str
    performed_by: str | None
    timestamp: datetime
