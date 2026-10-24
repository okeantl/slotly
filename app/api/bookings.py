from collections.abc import Sequence
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models import Booking, Master, Service
from app.models.booking import BookingStatus
from app.schemas.booking import BookingCreate, BookingRead

router = APIRouter(prefix="/bookings", tags=["bookings"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(data: BookingCreate, session: SessionDep) -> Booking:
    service = await session.get(Service, data.service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "service not found")

    master = await session.get(Master, data.master_id)
    if master is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "master not found")

    ends_at = data.starts_at + timedelta(minutes=service.duration_minutes)
    booking = Booking(
        master_id=data.master_id,
        client_id=data.client_id,
        service_id=service.id,
        during=Range(data.starts_at, ends_at),
        price_at_booking=service.price,
    )
    session.add(booking)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if "bookings_no_overlap" in str(exc.orig):
            raise HTTPException(status.HTTP_409_CONFLICT, "time slot is taken") from exc
        raise
    return booking


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(booking_id: int, session: SessionDep) -> Booking:
    booking = await session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "booking not found")
    return booking


@router.get("", response_model=list[BookingRead])
async def list_bookings(
    session: SessionDep,
    master_id: int | None = None,
    status_: Annotated[BookingStatus, Query(alias="status")] = BookingStatus.ACTIVE,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Sequence[Booking]:
    query = select(Booking).where(Booking.status == status_).order_by(Booking.during).limit(limit)
    if master_id is not None:
        query = query.where(Booking.master_id == master_id)
    result = await session.scalars(query)
    return result.all()
