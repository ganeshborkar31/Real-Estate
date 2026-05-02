from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.users.models import Permission, Role, User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def get_by_mobile(self, mobile_number: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.mobile_number == mobile_number)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(User.email == email)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(
            select(User)
            .order_by(desc(User.created_at))
            .offset(skip)
            .limit(limit)
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def add_role(self, user_id: str, role_id: str) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        role_result = await self.db.execute(select(Role).where(Role.id == role_id).options(selectinload(Role.permissions)))
        role = role_result.scalar_one_or_none()
        if not role:
            return None

        if role not in user.roles:
            user.roles.append(role)
            await self.db.commit()
            await self.db.refresh(user)

        return await self.get_by_id(user_id)

    async def remove_role(self, user_id: str, role_id: str) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.roles = [role for role in user.roles if role.id != role_id]
        await self.db.commit()
        await self.db.refresh(user)
        return await self.get_by_id(user_id)

    async def get_permissions_for_user(self, user_id: str) -> list[str]:
        user = await self.get_by_id(user_id)
        if not user:
            return []
        permissions = {permission.name for role in user.roles for permission in role.permissions}
        return sorted(list(permissions))
