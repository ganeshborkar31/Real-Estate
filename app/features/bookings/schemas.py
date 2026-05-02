from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

from enum import Enum


class BookingType(str, Enum):
    visit = "visit"
    reserve = "reserve"
    deal = "deal"


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"
    expired = "expired"


class BookingCreate(BaseModel):
    property_id: UUID
    booking_type: BookingType
    scheduled_at: Optional[datetime] = None
    message: Optional[str] = None


class BookingResponse(BaseModel):
    id: UUID
    property_id: UUID
    status: BookingStatus
    booking_type: BookingType
    scheduled_at: Optional[datetime]

    class Config:
        from_attributes = True


class BookingAction(BaseModel):
    action: str  # accept / reject
    reason: Optional[str] = None


class BookingReschedule(BaseModel):
    scheduled_at: datetime


class BookingClose(BaseModel):
    final_price: float