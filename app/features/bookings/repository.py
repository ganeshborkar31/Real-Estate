from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from .models import Booking


class BookingRepository:

    @staticmethod
    async def create(db: AsyncSession, booking: Booking):
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking

    @staticmethod
    async def get_by_id(db: AsyncSession, booking_id: UUID):
        result = await db.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: UUID):
        result = await db.execute(
            select(Booking).where(
                (Booking.buyer_id == user_id) | (Booking.owner_id == user_id)
            )
        )
        return result.scalars().all()

    @staticmethod
    async def save(db: AsyncSession, booking: Booking):
        await db.commit()
        await db.refresh(booking)
        return booking