from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis_client import (
    key_otp,
    key_otp_attempts,
    key_otp_requests,
    key_user_permissions,
    key_user_roles,
)
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_refresh_token,
    generate_otp,
    hash_otp,
    verify_email_token,
    verify_otp,
    verify_token,
)
from app.features.rbac.repository import RoleRepository
from app.features.users.service import UserService
from app.integrations.sms import SMSProviderError, send_otp_sms_india
from app.integrations.email import EmailProviderError, send_verification_email


class AuthService:
    def __init__(self, db: AsyncSession, redis_client: Redis):
        self.db = db
        self.redis = redis_client
        self.user_service = UserService(db)
        self.role_repo = RoleRepository(db)
        self.settings = get_settings()

    async def _get_or_compute_access(self, user_id: str, *, force_refresh: bool = False) -> tuple[list[str], list[str]]:
        if not force_refresh:
            cached_roles = await self.redis.get(key_user_roles(user_id))
            cached_permissions = await self.redis.get(key_user_permissions(user_id))
            if cached_roles is not None and cached_permissions is not None:
                roles = [r for r in cached_roles.split(",") if r]
                permissions = [p for p in cached_permissions.split(",") if p]
                return roles, permissions

        user = await self.user_service.get_user(user_id)
        roles = self.user_service.get_role_names(user)
        permissions = self.user_service.get_permission_names(user)

        ttl_seconds = self.settings.permission_cache_ttl_hours * 3600
        await self.redis.setex(key_user_roles(user_id), ttl_seconds, ",".join(roles))
        await self.redis.setex(key_user_permissions(user_id), ttl_seconds, ",".join(permissions))

        return roles, permissions

    async def send_otp(self, mobile_number: str) -> dict:
        requests_key = key_otp_requests(mobile_number)
        requests_count = await self.redis.incr(requests_key)
        if requests_count == 1:
            await self.redis.expire(requests_key, 3600)

        if requests_count > self.settings.otp_max_requests_per_hour:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP requests")

        otp = generate_otp()
        await self.redis.setex(key_otp(mobile_number), self.settings.otp_expire_minutes * 60, hash_otp(otp))
        await self.redis.setex(key_otp_attempts(mobile_number), self.settings.otp_expire_minutes * 60, "0")
        try:
            await send_otp_sms_india(mobile_number, otp)
        except SMSProviderError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        return {
            "message": "OTP sent successfully",
            "expires_in": self.settings.otp_expire_minutes * 60,
            "otp": otp if self.settings.env != "production" else None,
        }

    async def verify_otp(self, mobile_number: str, otp: str, full_name: str | None = None) -> dict:
        attempts_key = key_otp_attempts(mobile_number)
        attempts = int(await self.redis.get(attempts_key) or 0)
        if attempts >= self.settings.otp_max_attempts:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP attempts")

        stored_hash = await self.redis.get(key_otp(mobile_number))
        if not stored_hash:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not found")

        if not verify_otp(otp, stored_hash):
            await self.redis.incr(attempts_key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

        await self.redis.delete(key_otp(mobile_number))
        await self.redis.delete(attempts_key)

        user = await self.user_service.get_user_by_mobile(mobile_number)
        if not user:
            user = await self.user_service.register_user(mobile_number=mobile_number, full_name=full_name)
            buyer_role = await self.role_repo.get_by_name("buyer")
            if buyer_role:
                user = await self.user_service.add_role_to_user(user.id, buyer_role.id)

        user.is_mobile_verified = True
        await self.user_service.repo.update(user)

        roles, permissions = await self._get_or_compute_access(user.id, force_refresh=True)
        access_token = create_access_token(user.id, roles, permissions)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.settings.access_token_expire_minutes * 60,
        }

    async def refresh_access_token(self, refresh_token: str) -> dict:
        payload = verify_token(refresh_token)
        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user_id = payload.get("user_id")
        user = await self.user_service.get_user(user_id)
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

        roles, permissions = await self._get_or_compute_access(user_id)
        return {
            "access_token": create_access_token(user_id, roles, permissions),
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.settings.access_token_expire_minutes * 60,
        }

    async def send_email_verification(self, user_id: str, email: str) -> dict:
        user = await self.user_service.update_self(user_id, email=email)
        token = create_email_verification_token(user.email)
        await self.redis.setex(f"email_verification:{token}", 24 * 3600, user.id)
        verification_link = f"{self.settings.frontend_base_url.rstrip('/')}/verify-email?token={token}"
        try:
            await send_verification_email(user.email, verification_link)
        except EmailProviderError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
        return {
            "message": "Email verification sent",
            "verification_link": verification_link if self.settings.env != "production" else None,
            "token": token if self.settings.env != "production" else None,
        }

    async def verify_email(self, token: str) -> None:
        email = verify_email_token(token)
        user = await self.user_service.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found for this email")
        user.is_email_verified = True
        await self.user_service.repo.update(user)
