from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PropertyPurpose(str, Enum):
    SALE = "sale"
    RENT = "rent"


class PropertyType(str, Enum):
    FLAT = "flat"
    HOUSE = "house"
    VILLA = "villa"
    PLOT = "plot"
    LAND = "land"
    COMMERCIAL = "commercial"
    OFFICE = "office"
    SHOP = "shop"


class PropertyStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"
    SOLD = "sold"
    RENTED = "rented"


class FurnishingType(str, Enum):
    FURNISHED = "furnished"
    SEMI_FURNISHED = "semi_furnished"
    UNFURNISHED = "unfurnished"


class ParkingType(str, Enum):
    NONE = "none"
    BIKE = "bike"
    CAR = "car"
    BOTH = "both"


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        Index("ix_properties_city", "city"),
        Index("ix_properties_price", "price"),
        Index("ix_properties_property_type", "property_type"),
        Index("ix_properties_purpose", "purpose"),
        Index("ix_properties_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    listed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    purpose: Mapped[PropertyPurpose] = mapped_column(SQLEnum(PropertyPurpose, name="property_purpose"), nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(SQLEnum(PropertyType, name="property_type"), nullable=False)

    price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    price_per_sqft: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    price_negotiable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    security_deposit: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    maintenance_charge: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)

    area_sqft: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    carpet_area: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    builtup_area: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    plot_area: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    balconies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    floor_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    facing: Mapped[str | None] = mapped_column(String(50), nullable=True)
    age_of_property: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)

    furnishing: Mapped[FurnishingType | None] = mapped_column(SQLEnum(FurnishingType, name="furnishing_type"), nullable=True)
    parking: Mapped[ParkingType | None] = mapped_column(SQLEnum(ParkingType, name="parking_type"), nullable=True)
    water_supply: Mapped[str | None] = mapped_column(String(100), nullable=True)
    power_backup: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gated_security: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lift: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    gym: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    swimming_pool: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    garden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    address: Mapped[str] = mapped_column(String(500), nullable=False)
    locality: Mapped[str] = mapped_column(String(200), nullable=False)
    landmark: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    pincode: Mapped[str] = mapped_column(String(20), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    ownership_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    property_documents_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    documents_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rera_registered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rera_number: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    rera_state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    project_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    possession_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    status: Mapped[PropertyStatus] = mapped_column(
        SQLEnum(PropertyStatus, name="property_status"), nullable=False, default=PropertyStatus.DRAFT
    )
    verification_status: Mapped[str] = mapped_column(String(40), nullable=False, default="unverified")
    trust_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    views_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inquiries_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")
    listed_by_user = relationship("User", foreign_keys=[listed_by], lazy="joined")
    verified_by_user = relationship("User", foreign_keys=[verified_by], lazy="joined")
    approved_by_user = relationship("User", foreign_keys=[approved_by], lazy="joined")

    images: Mapped[list[PropertyImage]] = relationship(
        "PropertyImage", back_populates="property", lazy="selectin", cascade="all, delete-orphan"
    )
    amenities: Mapped[list[Amenity]] = relationship(
        "Amenity", secondary="property_amenities", back_populates="properties", lazy="selectin"
    )
    favorites: Mapped[list[Favorite]] = relationship(
        "Favorite", back_populates="property", lazy="selectin", cascade="all, delete-orphan"
    )
    inquiries: Mapped[list[Inquiry]] = relationship(
        "Inquiry", back_populates="property", lazy="selectin", cascade="all, delete-orphan"
    )
    project = relationship("Project", back_populates="properties", lazy="joined")
    documents = relationship("PropertyDocument", back_populates="property", lazy="selectin", cascade="all, delete-orphan")
    audit_logs = relationship("PropertyAuditLog", back_populates="property", lazy="selectin", cascade="all, delete-orphan")


class PropertyImage(Base):
    __tablename__ = "property_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    property_id: Mapped[str] = mapped_column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1200), nullable=False)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False, default="image")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    property: Mapped[Property] = relationship("Property", back_populates="images")


class Amenity(Base):
    __tablename__ = "amenities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    properties: Mapped[list[Property]] = relationship(
        "Property", secondary="property_amenities", back_populates="amenities", lazy="selectin"
    )


class PropertyAmenity(Base):
    __tablename__ = "property_amenities"

    property_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True
    )
    amenity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("amenities.id", ondelete="CASCADE"), primary_key=True
    )


class Inquiry(Base):
    __tablename__ = "inquiries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    property_id: Mapped[str] = mapped_column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    property: Mapped[Property] = relationship("Property", back_populates="inquiries")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "property_id", name="uq_favorites_user_property"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id: Mapped[str] = mapped_column(String(36), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    property: Mapped[Property] = relationship("Property", back_populates="favorites")
