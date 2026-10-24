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
from app.schemas.booking import BookingCreate, BookingRead, BookingUpdate

router = APIRouter(prefix="/bookings", tags=["bookings"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_booking_or_404(booking_id: int, session: SessionDep) -> Booking:
    booking = await session.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "booking not found")
    return booking


BookingDep = Annotated[Booking, Depends(get_booking_or_404)]


async def commit_or_409(session: AsyncSession) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        code = getattr(exc.orig, "sqlstate", None)
        if code == "23P01":
            raise HTTPException(status.HTTP_409_CONFLICT, "time slot is taken") from exc
        if code == "23503":
            raise HTTPException(status.HTTP_404_NOT_FOUND, "related object not found") from exc
        raise


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
    await commit_or_409(session)
    return booking


@router.get("/{booking_id}", response_model=BookingRead)
async def get_booking(booking: BookingDep) -> Booking:
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


@router.patch("/{booking_id}", response_model=BookingRead)
async def update_booking(booking: BookingDep, data: BookingUpdate, session: SessionDep) -> Booking:
    changes = data.model_dump(exclude_unset=True)

    if "status" in changes:
        booking.status = changes["status"]
    if "starts_at" in changes:
        service = await session.get(Service, booking.service_id)
        assert service is not None
        starts_at = changes["starts_at"]
        booking.during = Range(starts_at, starts_at + timedelta(minutes=service.duration_minutes))

    await commit_or_409(session)
    return booking
