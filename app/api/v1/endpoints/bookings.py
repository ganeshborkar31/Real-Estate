from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.core.security import get_current_user

from app.features.bookings import schemas, service, repository

router = APIRouter(prefix="/bookings", tags=["BOOKINGS"])


@router.post("/", response_model=schemas.BookingResponse)
async def create_booking(
    payload: schemas.BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    booking = await service.BookingService.create_booking(
        db, current_user.id, payload
    )
    return booking


@router.get("/")
async def list_bookings(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await repository.BookingRepository.list_by_user(db, current_user.id)


@router.get("/{booking_id}")
async def get_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    booking = await repository.BookingRepository.get_by_id(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.patch("/{booking_id}/respond")
async def respond_booking(
    booking_id: UUID,
    payload: schemas.BookingAction,
    db: AsyncSession = Depends(get_db),
):
    booking = await repository.BookingRepository.get_by_id(db, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")

    return await service.BookingService.respond_booking(
        db, booking, payload.action
    )


@router.patch("/{booking_id}/reschedule")
async def reschedule_booking(
    booking_id: UUID,
    payload: schemas.BookingReschedule,
    db: AsyncSession = Depends(get_db),
):
    booking = await repository.BookingRepository.get_by_id(db, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")

    return await service.BookingService.reschedule_booking(
        db, booking, payload.scheduled_at
    )


@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    booking = await repository.BookingRepository.get_by_id(db, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")

    return await service.BookingService.cancel_booking(db, booking)


@router.post("/{booking_id}/close")
async def close_booking(
    booking_id: UUID,
    payload: schemas.BookingClose,
    db: AsyncSession = Depends(get_db),
):
    booking = await repository.BookingRepository.get_by_id(db, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")

    return await service.BookingService.close_booking(
        db, booking, payload.final_price
    )