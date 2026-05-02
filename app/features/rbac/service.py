from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import key_user_permissions, key_user_roles
from app.features.rbac.repository import PermissionRepository, RoleRepository
from app.features.users.models import Permission, Role

DEFAULT_ROLES = [
    "buyer",
    "seller",
    "broker",
    "property_verifier",
    "salesperson",
    "area_manager",
    "regional_manager",
    "admin",
]

DEFAULT_PERMISSIONS = [
    "property:create",
    "property:view",
    "property:update",
    "property:verify",
    "property:approve",
    "property:delete",
    "document:verify",
    "lead:view",
    "lead:assign",
    "lead:convert",
    "user:view",
    "user:manage",
    "user:verify",
    "analytics:view",
]

ROLE_PERMISSION_MAP = {
    "property_verifier": ["property:view", "property:verify", "document:verify"],
    "salesperson": ["lead:view", "lead:convert"],
    "area_manager": ["lead:assign", "property:approve"],
    "regional_manager": ["user:view", "user:verify", "analytics:view"],
}


class RoleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RoleRepository(db)

    async def list_roles(self) -> list[Role]:
        return await self.repo.list_all()

    async def create_role(self, name: str, description: str | None = None) -> Role:
        existing = await self.repo.get_by_name(name)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
        role = Role(name=name, description=description)
        return await self.repo.create(role)

    async def assign_permission(self, role_id: str, permission_id: str) -> Role:
        role = await self.repo.add_permission(role_id, permission_id)
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role or permission not found")
        return role


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PermissionRepository(db)

    async def create_permission(self, name: str, description: str | None = None) -> Permission:
        existing = await self.repo.get_by_name(name)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Permission already exists")
        permission = Permission(name=name, description=description)
        return await self.repo.create(permission)


class RBACSeeder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.role_repo = RoleRepository(db)
        self.permission_repo = PermissionRepository(db)

    async def seed_defaults(self) -> None:
        permission_by_name: dict[str, Permission] = {}
        for perm_name in DEFAULT_PERMISSIONS:
            permission = await self.permission_repo.get_by_name(perm_name)
            if not permission:
                permission = Permission(name=perm_name, description=f"Default permission: {perm_name}")
                permission = await self.permission_repo.create(permission)
            permission_by_name[perm_name] = permission

        for role_name in DEFAULT_ROLES:
            role = await self.role_repo.get_by_name(role_name)
            if not role:
                role = Role(name=role_name, description=f"Default role: {role_name}")
                role = await self.role_repo.create(role)

        for role_name, permissions in ROLE_PERMISSION_MAP.items():
            role = await self.role_repo.get_by_name(role_name)
            if not role:
                continue
            for permission_name in permissions:
                permission = permission_by_name[permission_name]
                if permission not in role.permissions:
                    role.permissions.append(permission)
            await self.db.commit()
            await self.db.refresh(role)

        admin_role = await self.role_repo.get_by_name("admin")
        if admin_role:
            for permission in permission_by_name.values():
                if permission not in admin_role.permissions:
                    admin_role.permissions.append(permission)
            await self.db.commit()


async def invalidate_user_access_cache(redis_client, user_id: str) -> None:
    await redis_client.delete(key_user_permissions(user_id))
    await redis_client.delete(key_user_roles(user_id))
