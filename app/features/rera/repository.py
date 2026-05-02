from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.rera.models import Project, PropertyAuditLog, PropertyDocument


class RERARepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_by_id(self, project_id: str) -> Project | None:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_project_by_rera_number(self, rera_number: str) -> Project | None:
        result = await self.db.execute(select(Project).where(func.lower(Project.rera_number) == rera_number.lower()))
        return result.scalar_one_or_none()

    async def create_project(self, project: Project) -> Project:
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def add_document(self, document: PropertyDocument) -> PropertyDocument:
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def get_document_by_id(self, document_id: str) -> PropertyDocument | None:
        result = await self.db.execute(select(PropertyDocument).where(PropertyDocument.id == document_id))
        return result.scalar_one_or_none()

    async def list_property_documents(self, property_id: str) -> list[PropertyDocument]:
        result = await self.db.execute(select(PropertyDocument).where(PropertyDocument.property_id == property_id))
        return list(result.scalars().all())

    async def update_document(self, document: PropertyDocument) -> PropertyDocument:
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def add_audit_log(self, log: PropertyAuditLog) -> PropertyAuditLog:
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
