from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.properties.models import Property
from app.features.trust.models import Badge, PropertyBadge, UserBadge
from app.features.users.models import User


class BadgeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_badge(self, name: str, badge_type: str, color: str, description: str) -> Badge:
        result = await self.db.execute(select(Badge).where(Badge.name == name).where(Badge.badge_type == badge_type))
        badge = result.scalar_one_or_none()
        if badge:
            return badge
        badge = Badge(name=name, badge_type=badge_type, color=color, description=description)
        self.db.add(badge)
        await self.db.commit()
        await self.db.refresh(badge)
        return badge

    async def assign_property_badges(self, property_obj: Property) -> list[str]:
        names: list[str] = []
        if property_obj.rera_registered and property_obj.rera_number:
            names.append("RERA Verified")
        if property_obj.documents_verified or property_obj.property_documents_verified:
            names.append("Documents Verified")
        if property_obj.trust_score > 80:
            names.append("Highly Trusted")

        await self.db.execute(delete(PropertyBadge).where(PropertyBadge.property_id == property_obj.id))
        for name in names:
            color = "green" if name in {"RERA Verified", "Highly Trusted"} else "yellow"
            badge = await self._get_or_create_badge(name, "property", color, name)
            self.db.add(PropertyBadge(property_id=property_obj.id, badge_id=badge.id))
        await self.db.commit()
        return names

    async def assign_user_badges(self, user: User) -> list[str]:
        names: list[str] = []
        if user.is_agent_verified:
            names.append("Verified Agent")
        if user.trust_score > 70:
            names.append("Trusted Seller")
        if user.is_company_verified:
            names.append("Top Broker")

        await self.db.execute(delete(UserBadge).where(UserBadge.user_id == user.id))
        for name in names:
            color = "green" if name != "Trusted Seller" else "yellow"
            badge = await self._get_or_create_badge(name, "user", color, name)
            self.db.add(UserBadge(user_id=user.id, badge_id=badge.id))
        await self.db.commit()
        return names
