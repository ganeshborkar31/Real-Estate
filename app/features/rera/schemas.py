from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.features.rera.models import DocumentType, KYCType


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    rera_number: str = Field(min_length=3, max_length=120)
    state: str = Field(min_length=2, max_length=120)
    total_units: int | None = Field(default=None, ge=1)
    possession_date: date | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    builder_id: str
    rera_number: str
    state: str
    total_units: int | None
    possession_date: date | None
    is_rera_verified: bool
    created_at: datetime


class PropertyDocumentCreate(BaseModel):
    document_type: DocumentType
    file_url: str


class PropertyDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    property_id: str
    document_type: DocumentType
    file_url: str
    uploaded_by: str
    is_verified: bool
    verified_by: str | None
    created_at: datetime


class VerifyKYCRequest(BaseModel):
    kyc_type: KYCType
    kyc_document_url: str


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    property_id: str
    action: str
    performed_by: str | None
    metadata_json: dict[str, Any] | None
    timestamp: datetime
