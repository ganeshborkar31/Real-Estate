from __future__ import annotations

import re
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.properties.models import Property, PropertyStatus
from app.features.properties.repository import PropertyRepository
from app.features.rera.models import DocumentType, Project, PropertyAuditLog, PropertyDocument
from app.features.rera.repository import RERARepository
from app.features.rera.schemas import ProjectCreate, PropertyDocumentCreate
from app.features.users.service import UserService
from app.features.trust.badge_service import BadgeService
from app.features.trust.service import TrustService


class RERAService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RERARepository(db)
        self.property_repo = PropertyRepository(db)
        self.user_service = UserService(db)

    def validate_rera_number(self, rera_number: str, state: str) -> None:
        # Basic state-aware format guard for Indian RERA IDs.
        pattern = r"^[A-Za-z]{2}/[A-Za-z0-9\-]{6,30}$"
        if not re.match(pattern, rera_number):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RERA number format")
        if not rera_number.upper().startswith(state[:2].upper()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RERA number does not match state")

    async def check_duplicate_rera(self, rera_number: str) -> None:
        existing = await self.repo.get_project_by_rera_number(rera_number)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate RERA number detected")

    async def validate_project_registration(self, project_id: str | None) -> None:
        if not project_id:
            return
        project = await self.repo.get_project_by_id(project_id)
        if not project or not project.is_rera_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project RERA registration is not verified")

    async def create_project(self, builder_id: str, payload: ProjectCreate) -> Project:
        self.validate_rera_number(payload.rera_number, payload.state)
        await self.check_duplicate_rera(payload.rera_number)

        project = Project(
            name=payload.name,
            builder_id=builder_id,
            rera_number=payload.rera_number,
            state=payload.state,
            total_units=payload.total_units,
            possession_date=payload.possession_date,
            is_rera_verified=False,
        )
        return await self.repo.create_project(project)

    async def upload_document(self, property_id: str, uploaded_by: str, payload: PropertyDocumentCreate) -> PropertyDocument:
        property_obj = await self.property_repo.get_by_id(property_id)
        if not property_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

        document = PropertyDocument(
            property_id=property_id,
            document_type=payload.document_type,
            file_url=payload.file_url,
            uploaded_by=uploaded_by,
            is_verified=False,
        )
        created = await self.repo.add_document(document)
        await self._audit(property_id, "document_uploaded", uploaded_by, {"document_id": created.id})
        return created

    async def verify_document(self, document_id: str, verifier_id: str) -> PropertyDocument:
        document = await self.repo.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        document.is_verified = True
        document.verified_by = verifier_id
        updated = await self.repo.update_document(document)

        docs = await self.repo.list_property_documents(document.property_id)
        if docs and all(d.is_verified for d in docs):
            property_obj = await self.property_repo.get_by_id(document.property_id)
            if property_obj:
                property_obj.property_documents_verified = True
                property_obj.documents_verified = True
                await self.property_repo.update(property_obj)
                await TrustService(self.db).refresh_property_trust(property_obj, verifier_id)
                await BadgeService(self.db).assign_property_badges(property_obj)

        await self._audit(document.property_id, "document_verified", verifier_id, {"document_id": document.id})
        return updated

    async def verify_user_kyc(self, user_id: str, verifier_id: str, kyc_type: str, kyc_document_url: str):
        user = await self.user_service.get_user(user_id)
        user.kyc_verified = True
        user.kyc_type = kyc_type
        user.kyc_document_url = kyc_document_url
        user.kyc_verified_by = verifier_id
        user.kyc_verified_at = datetime.now(timezone.utc)
        updated = await self.user_service.repo.update(user)
        await TrustService(self.db).refresh_user_trust(updated, verifier_id)
        await BadgeService(self.db).assign_user_badges(updated)
        return updated

    async def enforce_property_compliance_for_approval(self, property_obj: Property) -> None:
        owner = await self.user_service.get_user(property_obj.owner_id)
        if not owner.kyc_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner KYC is not verified")

        docs = await self.repo.list_property_documents(property_obj.id)
        if not docs:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Required documents are missing")
        if not all(d.is_verified for d in docs):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All property documents must be verified")

        if property_obj.rera_registered and not property_obj.rera_number:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RERA number is required")

        if property_obj.project_id:
            await self.validate_project_registration(property_obj.project_id)

    async def enforce_property_compliance_for_submission(self, property_obj: Property) -> None:
        owner = await self.user_service.get_user(property_obj.owner_id)
        if not owner.kyc_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only KYC verified users can list properties")

    async def _audit(self, property_id: str, action: str, user_id: str | None, metadata: dict | None = None) -> None:
        await self.repo.add_audit_log(
            PropertyAuditLog(property_id=property_id, action=action, performed_by=user_id, metadata_json=metadata)
        )
