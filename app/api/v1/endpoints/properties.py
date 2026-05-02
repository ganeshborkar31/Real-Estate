from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, require_permission, verify_token
from app.db.session import get_db
from app.features.properties.models import FurnishingType, ParkingType, PropertyStatus, PropertyType, PropertyPurpose
from app.features.properties.schemas import (
    APIResponse,
    AddAmenitiesRequest,
    AddImagesRequest,
    AmenityOut,
    InquiryCreate,
    InquiryOut,
    PaginatedData,
    PropertyCreate,
    PropertyOut,
    PropertySearchParams,
    PropertyUpdate,
    RejectPropertyRequest,
)
from app.features.properties.service import PropertyService
from app.features.rera.schemas import PropertyDocumentCreate, PropertyDocumentOut
from app.features.rera.service import RERAService
from app.features.trust.service import TrustService

router = APIRouter(prefix="/properties", tags=["PROPERTIES"])
images_router = APIRouter(prefix="/images", tags=["PROPERTIES"])
amenities_router = APIRouter(prefix="/amenities", tags=["PROPERTIES"])
documents_router = APIRouter(prefix="/documents", tags=["PROPERTIES"])
optional_bearer = HTTPBearer(auto_error=False)
UUID_PATTERN = r"^[0-9a-fA-F-]{36}$"


def _is_admin_user(current_user: dict) -> bool:
    roles = set(current_user.get("roles", []))
    permissions = set(current_user.get("permissions", []))
    return "admin" in roles or "property:approve" in permissions


async def _property_out(db: AsyncSession, item) -> PropertyOut:
    verification_status = "verified" if item.status in {PropertyStatus.VERIFIED, PropertyStatus.APPROVED} else "unverified"
    document_status = "verified" if item.property_documents_verified else "pending"
    owner = getattr(item, "owner", None)
    kyc_status = "verified" if owner and getattr(owner, "kyc_verified", False) else "pending"
    payload = PropertyOut.model_validate(item).model_dump()
    payload["verification_status"] = verification_status
    payload["document_status"] = document_status
    payload["kyc_status"] = kyc_status
    badges = await TrustService(db).list_property_badges(item.id)
    payload["badges"] = [b.name for b in badges]
    return PropertyOut(**payload)


async def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer)) -> dict | None:
    if not credentials:
        return None
    payload = verify_token(credentials.credentials)
    if payload.get("token_type") != "access":
        return None
    return payload


@router.post("", response_model=APIResponse[PropertyOut], status_code=status.HTTP_201_CREATED)
async def create_property(
    payload: PropertyCreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:create")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).create_property(owner_id=current_user["user_id"], payload=payload)
    return APIResponse(data=await _property_out(db, property_obj), message="Property created successfully")


@router.get("/{property_id}", response_model=APIResponse[PropertyOut])
async def get_property_by_id(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    optional_user: dict | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    user_id = optional_user["user_id"] if optional_user else None
    is_admin = _is_admin_user(optional_user) if optional_user else False
    property_obj = await PropertyService(db).get_property_for_view(property_id, user_id, is_admin)
    return APIResponse(data=await _property_out(db, property_obj), message="Property fetched successfully")


@router.patch("/{property_id}", response_model=APIResponse[PropertyOut])
async def update_property(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    payload: PropertyUpdate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:update")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).update_property(
        property_id=property_id,
        actor_id=current_user["user_id"],
        payload=payload,
        is_admin=_is_admin_user(current_user),
    )
    return APIResponse(data=await _property_out(db, property_obj), message="Property updated successfully")


@router.delete("/{property_id}", response_model=APIResponse[PropertyOut])
async def delete_property(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:delete")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).soft_delete_property(
        property_id=property_id,
        actor_id=current_user["user_id"],
        is_admin=_is_admin_user(current_user),
    )
    return APIResponse(data=await _property_out(db, property_obj), message="Property deleted successfully")


@router.post("/{property_id}/submit", response_model=APIResponse[PropertyOut])
async def submit_property(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).submit_for_review(
        property_id=property_id,
        actor_id=current_user["user_id"],
        is_admin=_is_admin_user(current_user),
    )
    return APIResponse(data=await _property_out(db, property_obj), message="Property submitted for review")


@router.post("/{property_id}/verify", response_model=APIResponse[PropertyOut])
async def verify_property(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:verify")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).verify_property(property_id, current_user["user_id"])
    return APIResponse(data=await _property_out(db, property_obj), message="Property verified successfully")


@router.post("/{property_id}/approve", response_model=APIResponse[PropertyOut])
async def approve_property(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:approve")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).approve_property(property_id, current_user["user_id"])
    return APIResponse(data=await _property_out(db, property_obj), message="Property approved successfully")


@router.post("/{property_id}/reject", response_model=APIResponse[PropertyOut])
async def reject_property(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    payload: RejectPropertyRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:verify")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).reject_property(property_id, current_user["user_id"], payload.rejection_reason)
    return APIResponse(data=await _property_out(db, property_obj), message="Property rejected")


@router.post("/{property_id}/close", response_model=APIResponse[PropertyOut])
async def close_property(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).close_property(
        property_id,
        current_user["user_id"],
        is_admin=_is_admin_user(current_user),
    )
    return APIResponse(data=await _property_out(db, property_obj), message="Property closed successfully")


@router.get("", response_model=APIResponse[PaginatedData[PropertyOut]])
async def list_properties(
    city: str | None = None,
    locality: str | None = None,
    purpose: PropertyPurpose | None = None,
    property_type: PropertyType | None = None,
    price_min: float | None = Query(default=None, gt=0),
    price_max: float | None = Query(default=None, gt=0),
    bedrooms: int | None = Query(default=None, ge=0),
    bathrooms: int | None = Query(default=None, ge=0),
    furnishing: FurnishingType | None = None,
    parking: ParkingType | None = None,
    is_featured: bool | None = None,
    min_trust_score: int | None = Query(default=None, ge=0, le=100),
    verification_status: str | None = None,
    has_rera: bool | None = None,
    status_filter: PropertyStatus | None = Query(default=PropertyStatus.APPROVED, alias="status"),
    sort: str = Query(default="newest"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    optional_user: dict | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaginatedData[PropertyOut]]:
    params = PropertySearchParams(
        city=city,
        locality=locality,
        purpose=purpose,
        property_type=property_type,
        price_min=price_min,
        price_max=price_max,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        furnishing=furnishing,
        parking=parking,
        is_featured=is_featured,
        min_trust_score=min_trust_score,
        verification_status=verification_status,
        has_rera=has_rera,
        status=status_filter,
        sort=sort,
        page=page,
        limit=limit,
    )
    is_admin = _is_admin_user(optional_user) if optional_user else False
    properties, total = await PropertyService(db).search_properties(params, is_admin=is_admin)
    data = PaginatedData[PropertyOut](
        items=[await _property_out(db, item) for item in properties],
        page=page,
        limit=limit,
        total=total,
    )
    return APIResponse(data=data, message="Properties fetched successfully")


@router.get("/me", response_model=APIResponse[PaginatedData[PropertyOut]])
async def my_properties(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaginatedData[PropertyOut]]:
    properties, total = await PropertyService(db).list_my_properties(current_user["user_id"], page, limit)
    data = PaginatedData[PropertyOut](
        items=[await _property_out(db, item) for item in properties],
        page=page,
        limit=limit,
        total=total,
    )
    return APIResponse(data=data, message="My properties fetched successfully")


@router.get("/featured", response_model=APIResponse[PaginatedData[PropertyOut]])
async def featured_properties(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PaginatedData[PropertyOut]]:
    params = PropertySearchParams(is_featured=True, status=PropertyStatus.APPROVED, page=page, limit=limit)
    properties, total = await PropertyService(db).search_properties(params, is_admin=False)
    data = PaginatedData[PropertyOut](items=[await _property_out(db, item) for item in properties], page=page, limit=limit, total=total)
    return APIResponse(data=data, message="Featured properties fetched successfully")


@router.post("/{property_id}/images", response_model=APIResponse[PropertyOut])
async def add_images(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    payload: AddImagesRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:update")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).add_images(
        property_id,
        current_user["user_id"],
        payload,
        is_admin=_is_admin_user(current_user),
    )
    return APIResponse(data=await _property_out(db, property_obj), message="Property images uploaded successfully")


@router.post("/{property_id}/amenities", response_model=APIResponse[PropertyOut])
async def add_amenities(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    payload: AddAmenitiesRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:update")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyOut]:
    property_obj = await PropertyService(db).add_amenities(
        property_id,
        current_user["user_id"],
        payload.amenity_ids,
        is_admin=_is_admin_user(current_user),
    )
    return APIResponse(data=await _property_out(db, property_obj), message="Amenities updated successfully")


@amenities_router.get("", response_model=APIResponse[list[AmenityOut]])
async def list_amenities(db: AsyncSession = Depends(get_db)) -> APIResponse[list[AmenityOut]]:
    items = await PropertyService(db).list_amenities()
    return APIResponse(data=[AmenityOut.model_validate(item) for item in items], message="Amenities fetched successfully")


@router.post("/{property_id}/inquiries", response_model=APIResponse[InquiryOut], status_code=status.HTTP_201_CREATED)
async def create_inquiry(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    payload: InquiryCreate,
    optional_user: dict | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[InquiryOut]:
    user_id = optional_user["user_id"] if optional_user else None
    inquiry = await PropertyService(db).create_inquiry(
        property_id,
        user_id=user_id,
        message=payload.message,
        contact_number=payload.contact_number,
    )
    return APIResponse(data=InquiryOut.model_validate(inquiry), message="Inquiry created successfully")


@router.post("/{property_id}/documents", response_model=APIResponse[PropertyDocumentOut], status_code=status.HTTP_201_CREATED)
async def upload_document(
    property_id: Annotated[str, Path(pattern=UUID_PATTERN)],
    payload: PropertyDocumentCreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:update")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyDocumentOut]:
    document = await RERAService(db).upload_document(property_id, current_user["user_id"], payload)
    return APIResponse(data=PropertyDocumentOut.model_validate(document), message="Document uploaded successfully")


@images_router.delete("/{image_id}", response_model=APIResponse[dict])
async def delete_image(
    image_id: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("property:update")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    await PropertyService(db).delete_image(image_id, current_user["user_id"], is_admin=_is_admin_user(current_user))
    return APIResponse(data={"image_id": image_id}, message="Image deleted successfully")


@documents_router.post("/{document_id}/verify", response_model=APIResponse[PropertyDocumentOut])
async def verify_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("document:verify")),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PropertyDocumentOut]:
    document = await RERAService(db).verify_document(document_id, current_user["user_id"])
    return APIResponse(data=PropertyDocumentOut.model_validate(document), message="Document verified successfully")
