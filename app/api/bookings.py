from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models import Booking, Master, Service
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
