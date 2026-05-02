from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.properties.models import Amenity, Inquiry, Property, PropertyImage, PropertyStatus
from app.features.properties.schemas import PropertySearchParams


class PropertyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self) -> Select[tuple[Property]]:
        return select(Property).options(selectinload(Property.images), selectinload(Property.amenities))

    def _apply_filters(self, query: Select[tuple[Property]], params: PropertySearchParams) -> Select[tuple[Property]]:
        if params.city:
            query = query.where(func.lower(Property.city) == params.city.lower())
        if params.locality:
            query = query.where(func.lower(Property.locality) == params.locality.lower())
        if params.purpose:
            query = query.where(Property.purpose == params.purpose)
        if params.property_type:
            query = query.where(Property.property_type == params.property_type)
        if params.price_min is not None:
            query = query.where(Property.price >= params.price_min)
        if params.price_max is not None:
            query = query.where(Property.price <= params.price_max)
        if params.bedrooms is not None:
            query = query.where(Property.bedrooms == params.bedrooms)
        if params.bathrooms is not None:
            query = query.where(Property.bathrooms == params.bathrooms)
        if params.furnishing:
            query = query.where(Property.furnishing == params.furnishing)
        if params.parking:
            query = query.where(Property.parking == params.parking)
        if params.is_featured is not None:
            query = query.where(Property.is_featured == params.is_featured)
        if params.min_trust_score is not None:
            query = query.where(Property.trust_score >= params.min_trust_score)
        if params.has_rera is not None:
            query = query.where(Property.rera_registered == params.has_rera)
        if params.verification_status:
            query = query.where(Property.verification_status == params.verification_status)
        if params.status:
            query = query.where(Property.status == params.status)
        return query

    async def create(self, property_obj: Property) -> Property:
        self.db.add(property_obj)
        await self.db.commit()
        await self.db.refresh(property_obj)
        return property_obj

    async def get_by_id(self, property_id: str) -> Property | None:
        result = await self.db.execute(self._base_query().where(Property.id == property_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Property | None:
        result = await self.db.execute(select(Property).where(Property.slug == slug))
        return result.scalar_one_or_none()

    async def search(self, params: PropertySearchParams) -> tuple[list[Property], int]:
        query = self._apply_filters(self._base_query().where(Property.is_active.is_(True)), params)
        count_query = select(func.count()).select_from(query.subquery())

        if params.sort == "price_low_to_high":
            query = query.order_by(Property.price.asc(), Property.trust_score.desc())
        elif params.sort == "price_high_to_low":
            query = query.order_by(Property.price.desc(), Property.trust_score.desc())
        elif params.sort == "most_viewed":
            query = query.order_by(Property.views_count.desc(), Property.trust_score.desc())
        else:
            query = query.order_by(Property.trust_score.desc(), Property.created_at.desc())

        offset = (params.page - 1) * params.limit
        query = query.offset(offset).limit(params.limit)

        total_result = await self.db.execute(count_query)
        total = int(total_result.scalar_one())

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def list_for_owner(self, owner_id: str, page: int, limit: int) -> tuple[list[Property], int]:
        query = self._base_query().where(Property.owner_id == owner_id).where(Property.is_active.is_(True))
        total_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = int(total_result.scalar_one())
        result = await self.db.execute(query.order_by(Property.created_at.desc()).offset((page - 1) * limit).limit(limit))
        return list(result.scalars().all()), total

    async def update(self, property_obj: Property) -> Property:
        await self.db.commit()
        await self.db.refresh(property_obj)
        return property_obj

    async def get_amenities_by_ids(self, amenity_ids: list[str]) -> list[Amenity]:
        if not amenity_ids:
            return []
        result = await self.db.execute(select(Amenity).where(Amenity.id.in_(amenity_ids)))
        return list(result.scalars().all())

    async def list_amenities(self) -> list[Amenity]:
        result = await self.db.execute(select(Amenity).order_by(Amenity.name.asc()))
        return list(result.scalars().all())

    async def replace_images(self, property_obj: Property, images: list[PropertyImage]) -> None:
        property_obj.images.clear()
        property_obj.images.extend(images)

    async def add_images(self, property_obj: Property, images: list[PropertyImage]) -> Property:
        property_obj.images.extend(images)
        await self.db.commit()
        await self.db.refresh(property_obj)
        return property_obj

    async def get_image_by_id(self, image_id: str) -> PropertyImage | None:
        result = await self.db.execute(select(PropertyImage).where(PropertyImage.id == image_id))
        return result.scalar_one_or_none()

    async def delete_image(self, image: PropertyImage) -> None:
        await self.db.delete(image)
        await self.db.commit()

    async def create_inquiry(self, inquiry: Inquiry) -> Inquiry:
        self.db.add(inquiry)
        await self.db.commit()
        await self.db.refresh(inquiry)
        return inquiry

    async def increment_views(self, property_obj: Property) -> Property:
        property_obj.views_count += 1
        await self.db.commit()
        await self.db.refresh(property_obj)
        return property_obj
