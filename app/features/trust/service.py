from __future__ import annotations

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import key_property_trust_score, key_user_trust_score
from app.features.properties.models import Property
from app.features.trust.models import Badge, PropertyBadge, TrustAuditLog, UserBadge
from app.features.users.models import User


class TrustService:
    def __init__(self, db: AsyncSession, redis_client: Redis | None = None):
        self.db = db
        self.redis = redis_client

    def trust_level_from_score(self, score: int) -> str:
        if score >= 90:
            return "fully_verified"
        if score >= 75:
            return "rera_verified"
        if score >= 60:
            return "documents_verified"
        if score >= 40:
            return "basic_verified"
        return "unverified"

    async def compute_property_trust(self, property_obj: Property) -> tuple[int, str]:
        score = 0
        if property_obj.rera_registered and property_obj.rera_number:
            score += 40
        if property_obj.documents_verified or property_obj.property_documents_verified:
            score += 30
        owner = property_obj.owner
        if owner and owner.kyc_verified:
            score += 10
        if len(property_obj.images) > 5:
            score += 10
        completeness = all([property_obj.description, property_obj.address, property_obj.locality, property_obj.city, property_obj.state])
        if completeness:
            score += 10
        score = min(100, score)
        level = self.trust_level_from_score(score)
        return score, level

    async def compute_user_trust(self, user: User) -> tuple[int, str]:
        score = 0
        if user.kyc_verified:
            score += 40
        # placeholder signals until transaction/review systems are integrated
        if user.is_agent_verified:
            score += 20
        profile_complete = bool(user.full_name and user.email and user.mobile_number)
        if profile_complete:
            score += 20
        if user.is_company_verified:
            score += 20
        score = min(100, score)
        return score, self.trust_level_from_score(score)

    async def refresh_property_trust(self, property_obj: Property, performed_by: str | None = None) -> tuple[int, str]:
        score, level = await self.compute_property_trust(property_obj)
        property_obj.trust_score = score
        property_obj.verification_status = level
        await self.db.commit()
        await self.db.refresh(property_obj)
        if self.redis:
            await self.redis.setex(key_property_trust_score(property_obj.id), 3600, str(score))
        await self.add_audit_log("property", property_obj.id, "updated", performed_by)
        return score, level

    async def refresh_user_trust(self, user: User, performed_by: str | None = None) -> tuple[int, str]:
        score, level = await self.compute_user_trust(user)
        user.trust_score = score
        await self.db.commit()
        await self.db.refresh(user)
        if self.redis:
            await self.redis.setex(key_user_trust_score(user.id), 3600, str(score))
        await self.add_audit_log("user", user.id, "updated", performed_by)
        return score, level

    async def add_audit_log(self, entity_type: str, entity_id: str, action: str, performed_by: str | None) -> None:
        self.db.add(TrustAuditLog(entity_type=entity_type, entity_id=entity_id, action=action, performed_by=performed_by))
        await self.db.commit()

    async def list_property_badges(self, property_id: str) -> list[Badge]:
        result = await self.db.execute(
            select(Badge)
            .join(PropertyBadge, PropertyBadge.badge_id == Badge.id)
            .where(PropertyBadge.property_id == property_id)
        )
        return list(result.scalars().all())

    async def list_user_badges(self, user_id: str) -> list[Badge]:
        result = await self.db.execute(
            select(Badge)
            .join(UserBadge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id)
        )
        return list(result.scalars().all())
