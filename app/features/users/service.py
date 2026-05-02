from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.users.models import User
from app.features.users.repository import UserRepository


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def get_user(self, user_id: str) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def get_user_by_mobile(self, mobile_number: str) -> User | None:
        return await self.repo.get_by_mobile(mobile_number)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email)

    async def register_user(self, mobile_number: str, full_name: str | None = None, email: str | None = None) -> User:
        existing = await self.repo.get_by_mobile(mobile_number)
        if existing:
            return existing

        if email:
            email_owner = await self.repo.get_by_email(email)
            if email_owner:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

        user = User(
            mobile_number=mobile_number,
            full_name=full_name,
            email=email,
            is_mobile_verified=False,
            is_email_verified=False,
            is_active=True,
        )
        return await self.repo.create(user)

    async def update_self(self, user_id: str, full_name: str | None = None, email: str | None = None) -> User:
        user = await self.get_user(user_id)

        if full_name is not None:
            user.full_name = full_name

        if email is not None and email != user.email:
            email_owner = await self.repo.get_by_email(email)
            if email_owner and email_owner.id != user_id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")
            user.email = email
            user.is_email_verified = False

        return await self.repo.update(user)

    def get_role_names(self, user: User) -> list[str]:
        return sorted([role.name for role in user.roles])

    def get_permission_names(self, user: User) -> list[str]:
        permissions = {permission.name for role in user.roles for permission in role.permissions}
        return sorted(list(permissions))

    async def add_role_to_user(self, user_id: str, role_id: str) -> User:
        user = await self.repo.add_role(user_id, role_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or role not found")
        return user
