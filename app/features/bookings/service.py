from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from .models import Booking, BookingStatus, BookingType
from .repository import BookingRepository


class BookingService:

    @staticmethod
    async def create_booking(db: AsyncSession, buyer_id: UUID, data):
        booking = Booking(
            property_id=data.property_id,
            buyer_id=buyer_id,
            owner_id=buyer_id,  # TODO: fetch property owner
            booking_type=data.booking_type,
            scheduled_at=data.scheduled_at,
            visit_notes=data.message,
        )
        return await BookingRepository.create(db, booking)

    @staticmethod
    async def respond_booking(db: AsyncSession, booking: Booking, action: str):
        if action == "accept":
            booking.status = BookingStatus.confirmed
        elif action == "reject":
            booking.status = BookingStatus.cancelled

        return await BookingRepository.save(db, booking)

    @staticmethod
    async def reschedule_booking(db: AsyncSession, booking: Booking, new_time: datetime):
        booking.scheduled_at = new_time
        booking.status = BookingStatus.pending
        return await BookingRepository.save(db, booking)

    @staticmethod
    async def cancel_booking(db: AsyncSession, booking: Booking):
        booking.status = BookingStatus.cancelled
        return await BookingRepository.save(db, booking)

    @staticmethod
    async def close_booking(db: AsyncSession, booking: Booking, final_price: float):
        booking.final_price = final_price
        booking.status = BookingStatus.completed
        return await BookingRepository.save(db, booking)