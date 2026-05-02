from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.users.models import Permission, Role


class RoleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: str) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.id == role_id).options(selectinload(Role.permissions)))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.db.execute(select(Role).where(Role.name == name).options(selectinload(Role.permissions)))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        result = await self.db.execute(select(Role).options(selectinload(Role.permissions)).order_by(Role.name.asc()))
        return list(result.scalars().all())

    async def create(self, role: Role) -> Role:
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role

    async def add_permission(self, role_id: str, permission_id: str) -> Role | None:
        role = await self.get_by_id(role_id)
        if not role:
            return None
        permission_result = await self.db.execute(select(Permission).where(Permission.id == permission_id))
        permission = permission_result.scalar_one_or_none()
        if not permission:
            return None
        if permission not in role.permissions:
            role.permissions.append(permission)
            await self.db.commit()
            await self.db.refresh(role)
        return await self.get_by_id(role_id)


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_name(self, name: str) -> Permission | None:
        result = await self.db.execute(select(Permission).where(Permission.name == name))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Permission]:
        result = await self.db.execute(select(Permission).order_by(Permission.name.asc()))
        return list(result.scalars().all())

    async def create(self, permission: Permission) -> Permission:
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission

    async def get_by_id(self, permission_id: str) -> Permission | None:
        result = await self.db.execute(select(Permission).where(Permission.id == permission_id))
        return result.scalar_one_or_none()
