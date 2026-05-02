from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.generics import GenericModel

from app.features.properties.models import FurnishingType, ParkingType, PropertyPurpose, PropertyStatus, PropertyType

SLUG_SANITIZE_REGEX = re.compile(r"[^a-z0-9-]+")


def generate_slug(value: str) -> str:
    slug = value.strip().lower().replace("&", "and")
    slug = re.sub(r"\s+", "-", slug)
    slug = SLUG_SANITIZE_REGEX.sub("", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


T = TypeVar("T")


class APIResponse(GenericModel, Generic[T]):
    success: bool = True
    data: T
    message: str


class PaginatedData(GenericModel, Generic[T]):
    items: list[T]
    page: int
    limit: int
    total: int


class PropertyImageInput(BaseModel):
    url: str
    media_type: Literal["image", "video"] = "image"
    is_primary: bool = False


class PropertyCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    slug: str | None = None
    description: str | None = None

    purpose: PropertyPurpose
    property_type: PropertyType

    price: Decimal = Field(gt=0)
    price_per_sqft: Decimal | None = Field(default=None, gt=0)
    price_negotiable: bool = False
    security_deposit: Decimal | None = Field(default=None, gt=0)
    maintenance_charge: Decimal | None = Field(default=None, ge=0)

    area_sqft: Decimal | None = Field(default=None, gt=0)
    carpet_area: Decimal | None = Field(default=None, gt=0)
    builtup_area: Decimal | None = Field(default=None, gt=0)
    plot_area: Decimal | None = Field(default=None, gt=0)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    balconies: int | None = Field(default=None, ge=0)
    floor_number: int | None = None
    total_floors: int | None = Field(default=None, ge=0)
    facing: str | None = None
    age_of_property: int | None = Field(default=None, ge=0)
    year_built: int | None = Field(default=None, ge=1800)

    furnishing: FurnishingType | None = None
    parking: ParkingType | None = None
    water_supply: str | None = None
    power_backup: bool = False
    gated_security: bool = False
    lift: bool = False
    gym: bool = False
    swimming_pool: bool = False
    garden: bool = False

    address: str = Field(min_length=3, max_length=500)
    locality: str = Field(min_length=2, max_length=200)
    landmark: str | None = None
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(min_length=2, max_length=120)
    pincode: str = Field(min_length=3, max_length=20)
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    ownership_type: str | None = None
    property_documents_verified: bool = False
    project_id: str | None = None
    rera_registered: bool = False
    rera_number: str | None = None
    rera_state: str | None = None
    project_name: str | None = None
    possession_date: date | None = None

    available_from: date | None = None
    is_available: bool = True

    rejection_reason: str | None = None

    is_featured: bool = False
    is_premium: bool = False

    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=500)

    amenity_ids: list[str] = Field(default_factory=list)
    images: list[PropertyImageInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_business_rules(self) -> "PropertyCreate":
        if self.property_type in {PropertyType.FLAT, PropertyType.HOUSE} and self.bedrooms is None:
            raise ValueError("bedrooms is required for flat and house")
        if len(self.images) > 20:
            raise ValueError("maximum 20 images are allowed")
        if self.rera_registered and not self.rera_number:
            raise ValueError("rera_number is required when rera_registered is true")
        return self


class PropertyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    slug: str | None = None
    description: str | None = None

    purpose: PropertyPurpose | None = None
    property_type: PropertyType | None = None

    price: Decimal | None = Field(default=None, gt=0)
    price_per_sqft: Decimal | None = Field(default=None, gt=0)
    price_negotiable: bool | None = None
    security_deposit: Decimal | None = Field(default=None, gt=0)
    maintenance_charge: Decimal | None = Field(default=None, ge=0)

    area_sqft: Decimal | None = Field(default=None, gt=0)
    carpet_area: Decimal | None = Field(default=None, gt=0)
    builtup_area: Decimal | None = Field(default=None, gt=0)
    plot_area: Decimal | None = Field(default=None, gt=0)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    balconies: int | None = Field(default=None, ge=0)
    floor_number: int | None = None
    total_floors: int | None = Field(default=None, ge=0)
    facing: str | None = None
    age_of_property: int | None = Field(default=None, ge=0)
    year_built: int | None = Field(default=None, ge=1800)

    furnishing: FurnishingType | None = None
    parking: ParkingType | None = None
    water_supply: str | None = None
    power_backup: bool | None = None
    gated_security: bool | None = None
    lift: bool | None = None
    gym: bool | None = None
    swimming_pool: bool | None = None
    garden: bool | None = None

    address: str | None = Field(default=None, min_length=3, max_length=500)
    locality: str | None = Field(default=None, min_length=2, max_length=200)
    landmark: str | None = None
    city: str | None = Field(default=None, min_length=2, max_length=120)
    state: str | None = Field(default=None, min_length=2, max_length=120)
    pincode: str | None = Field(default=None, min_length=3, max_length=20)
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    ownership_type: str | None = None
    property_documents_verified: bool | None = None
    project_id: str | None = None
    rera_registered: bool | None = None
    rera_number: str | None = None
    rera_state: str | None = None
    project_name: str | None = None
    possession_date: date | None = None
    available_from: date | None = None
    is_available: bool | None = None

    rejection_reason: str | None = None

    is_featured: bool | None = None
    is_premium: bool | None = None

    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, max_length=500)

    amenity_ids: list[str] | None = None
    images: list[PropertyImageInput] | None = None

    @model_validator(mode="after")
    def validate_image_count(self) -> "PropertyUpdate":
        if self.images is not None and len(self.images) > 20:
            raise ValueError("maximum 20 images are allowed")
        return self


class PropertySearchParams(BaseModel):
    city: str | None = None
    locality: str | None = None
    purpose: PropertyPurpose | None = None
    property_type: PropertyType | None = None
    price_min: Decimal | None = Field(default=None, gt=0)
    price_max: Decimal | None = Field(default=None, gt=0)
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    furnishing: FurnishingType | None = None
    parking: ParkingType | None = None
    is_featured: bool | None = None
    min_trust_score: int | None = Field(default=None, ge=0, le=100)
    has_rera: bool | None = None
    verification_status: str | None = None
    status: PropertyStatus | None = PropertyStatus.APPROVED
    sort: Literal["newest", "price_low_to_high", "price_high_to_low", "most_viewed"] = "newest"
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class PropertyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    listed_by: str | None
    title: str
    slug: str
    description: str | None
    purpose: PropertyPurpose
    property_type: PropertyType
    price: Decimal
    city: str
    locality: str
    state: str
    status: PropertyStatus
    project_id: str | None
    rera_registered: bool
    rera_number: str | None
    rera_state: str | None
    project_name: str | None
    possession_date: date | None
    is_available: bool
    is_active: bool
    property_documents_verified: bool
    verification_status: str
    document_status: str
    kyc_status: str
    badges: list[str] = Field(default_factory=list)
    views_count: int
    inquiries_count: int
    is_featured: bool
    is_premium: bool
    created_at: datetime
    updated_at: datetime


class AmenityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str | None


class PropertyImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    property_id: str
    url: str
    media_type: str
    is_primary: bool
    created_at: datetime


class AddAmenitiesRequest(BaseModel):
    amenity_ids: list[str] = Field(default_factory=list)


class AddImagesRequest(BaseModel):
    images: list[PropertyImageInput]

    @model_validator(mode="after")
    def validate_image_count(self) -> "AddImagesRequest":
        if len(self.images) > 20:
            raise ValueError("maximum 20 images are allowed")
        return self


class RejectPropertyRequest(BaseModel):
    rejection_reason: str = Field(min_length=3)


class InquiryCreate(BaseModel):
    message: str | None = None
    contact_number: str | None = Field(default=None, max_length=20)


class InquiryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    property_id: str
    user_id: str | None
    message: str | None
    contact_number: str | None
    created_at: datetime
