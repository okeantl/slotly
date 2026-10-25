from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.models import Salon
from app.schemas.salon import SalonCreate, SalonRead

router = APIRouter(prefix="/salons", tags=["salons"])


async def get_salon_or_404(salon_id: int, session: SessionDep) -> Salon:
    salon = await session.get(Salon, salon_id)
    if salon is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "salon not found")
    return salon


SalonDep = Annotated[Salon, Depends(get_salon_or_404)]


@router.post("", response_model=SalonRead, status_code=status.HTTP_201_CREATED)
async def create_salon(data: SalonCreate, session: SessionDep) -> Salon:
    salon = Salon(**data.model_dump())
    session.add(salon)
    await session.commit()
    return salon


@router.get("/{salon_id}", response_model=SalonRead)
async def get_salon(salon: SalonDep) -> Salon:
    return salon


@router.get("", response_model=list[SalonRead])
async def list_salons(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Sequence[Salon]:
    result = await session.scalars(select(Salon).order_by(Salon.id).limit(limit))
    return result.all()
