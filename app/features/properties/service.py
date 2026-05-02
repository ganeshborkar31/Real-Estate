from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.properties.models import Inquiry, Property, PropertyImage, PropertyStatus
from app.features.properties.repository import PropertyRepository
from app.features.properties.schemas import (
    AddImagesRequest,
    PropertyCreate,
    PropertySearchParams,
    PropertyUpdate,
    generate_slug,
)
from app.features.trust.badge_service import BadgeService
from app.features.trust.service import TrustService


class PropertyService:
    def __init__(self, db: AsyncSession):
        self.repo = PropertyRepository(db)

    async def create_property(self, owner_id: str, payload: PropertyCreate, listed_by_id: str | None = None) -> Property:
        slug = payload.slug or generate_slug(payload.title)
        slug = await self._build_unique_slug(slug)

        amenities = await self.repo.get_amenities_by_ids(payload.amenity_ids)
        images = [PropertyImage(url=i.url, media_type=i.media_type, is_primary=i.is_primary) for i in payload.images]

        property_obj = Property(
            owner_id=owner_id,
            listed_by=listed_by_id,
            title=payload.title,
            slug=slug,
            description=payload.description,
            purpose=payload.purpose,
            property_type=payload.property_type,
            price=payload.price,
            price_per_sqft=payload.price_per_sqft,
            price_negotiable=payload.price_negotiable,
            security_deposit=payload.security_deposit,
            maintenance_charge=payload.maintenance_charge,
            area_sqft=payload.area_sqft,
            carpet_area=payload.carpet_area,
            builtup_area=payload.builtup_area,
            plot_area=payload.plot_area,
            bedrooms=payload.bedrooms,
            bathrooms=payload.bathrooms,
            balconies=payload.balconies,
            floor_number=payload.floor_number,
            total_floors=payload.total_floors,
            facing=payload.facing,
            age_of_property=payload.age_of_property,
            year_built=payload.year_built,
            furnishing=payload.furnishing,
            parking=payload.parking,
            water_supply=payload.water_supply,
            power_backup=payload.power_backup,
            gated_security=payload.gated_security,
            lift=payload.lift,
            gym=payload.gym,
            swimming_pool=payload.swimming_pool,
            garden=payload.garden,
            address=payload.address,
            locality=payload.locality,
            landmark=payload.landmark,
            city=payload.city,
            state=payload.state,
            pincode=payload.pincode,
            latitude=payload.latitude,
            longitude=payload.longitude,
            ownership_type=payload.ownership_type,
            property_documents_verified=payload.property_documents_verified,
            project_id=payload.project_id,
            rera_registered=payload.rera_registered,
            rera_number=payload.rera_number,
            rera_state=payload.rera_state,
            project_name=payload.project_name,
            possession_date=payload.possession_date,
            available_from=payload.available_from,
            is_available=payload.is_available,
            status=PropertyStatus.DRAFT,
            rejection_reason=payload.rejection_reason,
            is_featured=payload.is_featured,
            is_premium=payload.is_premium,
            meta_title=payload.meta_title,
            meta_description=payload.meta_description,
            amenities=amenities,
            images=images,
        )
        from app.features.rera.service import RERAService
        rera_service = RERAService(self.repo.db)
        await rera_service.enforce_property_compliance_for_submission(property_obj)
        created = await self.repo.create(property_obj)
        await TrustService(self.repo.db).refresh_property_trust(created, owner_id)
        await BadgeService(self.repo.db).assign_property_badges(created)
        await rera_service._audit(created.id, "created", owner_id, {"status": created.status.value})
        return created

    async def get_property_for_view(self, property_id: str, viewer_id: str | None, is_admin: bool) -> Property:
        property_obj = await self._get_or_404(property_id)

        can_view_private = bool(viewer_id and (viewer_id == property_obj.owner_id or is_admin))
        if (property_obj.status != PropertyStatus.APPROVED or not property_obj.is_active) and not can_view_private:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

        await self.repo.increment_views(property_obj)
        return property_obj

    async def update_property(self, property_id: str, actor_id: str, payload: PropertyUpdate, is_admin: bool = False) -> Property:
        property_obj = await self._get_or_404(property_id)
        self._assert_owner_or_admin(property_obj, actor_id, is_admin)

        if property_obj.status == PropertyStatus.APPROVED and not is_admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Approved properties cannot be edited")

        data = payload.model_dump(exclude_unset=True)
        amenity_ids = data.pop("amenity_ids", None)
        image_payloads = data.pop("images", None)

        if "title" in data and "slug" not in data:
            data["slug"] = await self._build_unique_slug(generate_slug(data["title"]), property_obj.id)
        elif "slug" in data and data["slug"]:
            data["slug"] = await self._build_unique_slug(generate_slug(data["slug"]), property_obj.id)

        for key, value in data.items():
            setattr(property_obj, key, value)

        if amenity_ids is not None:
            property_obj.amenities = await self.repo.get_amenities_by_ids(amenity_ids)

        if image_payloads is not None:
            images = [PropertyImage(url=i.url, media_type=i.media_type, is_primary=i.is_primary) for i in image_payloads]
            await self.repo.replace_images(property_obj, images)

        updated = await self.repo.update(property_obj)
        await TrustService(self.repo.db).refresh_property_trust(updated, actor_id)
        await BadgeService(self.repo.db).assign_property_badges(updated)
        from app.features.rera.service import RERAService
        await RERAService(self.repo.db)._audit(updated.id, "updated", actor_id, {"status": updated.status.value})
        return updated

    async def soft_delete_property(self, property_id: str, actor_id: str, is_admin: bool = False) -> Property:
        property_obj = await self._get_or_404(property_id)
        self._assert_owner_or_admin(property_obj, actor_id, is_admin)
        property_obj.is_active = False
        return await self.repo.update(property_obj)

    async def search_properties(self, params: PropertySearchParams, is_admin: bool = False) -> tuple[list[Property], int]:
        effective_params = params
        if not is_admin and (params.status is None or params.status != PropertyStatus.APPROVED):
            effective_params = params.model_copy(update={"status": PropertyStatus.APPROVED})
        return await self.repo.search(effective_params)

    async def list_my_properties(self, owner_id: str, page: int, limit: int) -> tuple[list[Property], int]:
        return await self.repo.list_for_owner(owner_id, page, limit)

    async def submit_for_review(self, property_id: str, actor_id: str, is_admin: bool = False) -> Property:
        property_obj = await self._get_or_404(property_id)
        self._assert_owner_or_admin(property_obj, actor_id, is_admin)
        if property_obj.status != PropertyStatus.DRAFT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft properties can be submitted")
        property_obj.status = PropertyStatus.PENDING
        from app.features.rera.service import RERAService
        await RERAService(self.repo.db)._audit(property_obj.id, "submitted", actor_id, None)
        return await self.repo.update(property_obj)

    async def verify_property(self, property_id: str, verifier_id: str) -> Property:
        property_obj = await self._get_or_404(property_id)
        if property_obj.status != PropertyStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending properties can be verified")
        property_obj.status = PropertyStatus.UNDER_REVIEW
        property_obj.verified_by = verifier_id
        from app.features.rera.service import RERAService
        await RERAService(self.repo.db)._audit(property_obj.id, "under_review", verifier_id, None)
        return await self.repo.update(property_obj)

    async def approve_property(self, property_id: str, approver_id: str) -> Property:
        property_obj = await self._get_or_404(property_id)
        if property_obj.status not in {PropertyStatus.UNDER_REVIEW, PropertyStatus.VERIFIED}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Property must be under review or verified")
        if property_obj.status == PropertyStatus.UNDER_REVIEW:
            property_obj.status = PropertyStatus.VERIFIED
        from app.features.rera.service import RERAService
        await RERAService(self.repo.db).enforce_property_compliance_for_approval(property_obj)
        property_obj.status = PropertyStatus.APPROVED
        property_obj.approved_by = approver_id
        property_obj.rejection_reason = None
        await RERAService(self.repo.db)._audit(property_obj.id, "approved", approver_id, None)
        return await self.repo.update(property_obj)

    async def reject_property(self, property_id: str, reviewer_id: str, reason: str) -> Property:
        property_obj = await self._get_or_404(property_id)
        property_obj.status = PropertyStatus.REJECTED
        property_obj.verified_by = reviewer_id
        property_obj.rejection_reason = reason
        from app.features.rera.service import RERAService
        await RERAService(self.repo.db)._audit(property_obj.id, "rejected", reviewer_id, {"reason": reason})
        return await self.repo.update(property_obj)

    async def close_property(self, property_id: str, actor_id: str, is_admin: bool = False) -> Property:
        property_obj = await self._get_or_404(property_id)
        self._assert_owner_or_admin(property_obj, actor_id, is_admin)
        property_obj.status = PropertyStatus.SOLD if property_obj.purpose.value == "sale" else PropertyStatus.RENTED
        property_obj.is_available = False
        return await self.repo.update(property_obj)

    async def add_amenities(self, property_id: str, actor_id: str, amenity_ids: list[str], is_admin: bool = False) -> Property:
        property_obj = await self._get_or_404(property_id)
        self._assert_owner_or_admin(property_obj, actor_id, is_admin)
        amenities = await self.repo.get_amenities_by_ids(amenity_ids)
        property_obj.amenities = amenities
        return await self.repo.update(property_obj)

    async def list_amenities(self):
        return await self.repo.list_amenities()

    async def add_images(self, property_id: str, actor_id: str, payload: AddImagesRequest, is_admin: bool = False) -> Property:
        property_obj = await self._get_or_404(property_id)
        self._assert_owner_or_admin(property_obj, actor_id, is_admin)

        if len(property_obj.images) + len(payload.images) > 20:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="maximum 20 images are allowed")

        new_images = [PropertyImage(url=i.url, media_type=i.media_type, is_primary=i.is_primary) for i in payload.images]
        if any(image.is_primary for image in new_images):
            for image in property_obj.images:
                image.is_primary = False
        updated = await self.repo.add_images(property_obj, new_images)
        await TrustService(self.repo.db).refresh_property_trust(updated, actor_id)
        await BadgeService(self.repo.db).assign_property_badges(updated)
        return updated

    async def delete_image(self, image_id: str, actor_id: str, is_admin: bool = False) -> None:
        image = await self.repo.get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

        property_obj = await self._get_or_404(image.property_id)
        self._assert_owner_or_admin(property_obj, actor_id, is_admin)
        await self.repo.delete_image(image)

    async def create_inquiry(
        self,
        property_id: str,
        user_id: str | None,
        message: str | None = None,
        contact_number: str | None = None,
    ) -> Inquiry:
        property_obj = await self._get_or_404(property_id)
        if property_obj.status != PropertyStatus.APPROVED or not property_obj.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inquiries allowed only for approved properties")

        inquiry = Inquiry(property_id=property_obj.id, user_id=user_id, message=message, contact_number=contact_number)
        created = await self.repo.create_inquiry(inquiry)
        property_obj.inquiries_count += 1
        await self.repo.update(property_obj)
        return created

    async def _get_or_404(self, property_id: str) -> Property:
        property_obj = await self.repo.get_by_id(property_id)
        if not property_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
        return property_obj

    async def _build_unique_slug(self, base_slug: str, current_property_id: str | None = None) -> str:
        slug = base_slug
        suffix = 1
        while True:
            existing = await self.repo.get_by_slug(slug)
            if not existing or existing.id == current_property_id:
                return slug
            suffix += 1
            slug = f"{base_slug}-{suffix}"

    def _assert_owner_or_admin(self, property_obj: Property, actor_id: str, is_admin: bool) -> None:
        if property_obj.owner_id != actor_id and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this property")
