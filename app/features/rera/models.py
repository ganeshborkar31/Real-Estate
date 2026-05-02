from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentType(str, Enum):
    OWNERSHIP_PROOF = "ownership_proof"
    SALE_DEED = "sale_deed"
    LAYOUT_PLAN = "layout_plan"
    APPROVAL_CERTIFICATE = "approval_certificate"
    BUILDER_LICENSE = "builder_license"


class KYCType(str, Enum):
    AADHAAR = "aadhaar"
    PAN = "pan"
    BUSINESS = "business"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    builder_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rera_number: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    total_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    possession_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_rera_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    properties = relationship("Property", back_populates="project", lazy="selectin")


class PropertyDocument(Base):
    __tablename__ = "property_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    property_id: Mapped[str] = mapped_column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type: Mapped[DocumentType] = mapped_column(SQLEnum(DocumentType, name="document_type"), nullable=False)
    file_url: Mapped[str] = mapped_column(String(1200), nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    property = relationship("Property", back_populates="documents")


class PropertyAuditLog(Base):
    __tablename__ = "property_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    property_id: Mapped[str] = mapped_column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    performed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    property = relationship("Property", back_populates="audit_logs")
