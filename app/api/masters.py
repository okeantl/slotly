from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep, commit_or_http_error
from app.models import Master
from app.schemas.master import MasterCreate, MasterRead, MasterUpdate

router = APIRouter(prefix="/masters", tags=["masters"])


async def get_master_or_404(master_id: int, session: SessionDep) -> Master:
    master = await session.get(Master, master_id)
    if master is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "master not found")
    return master


MasterDep = Annotated[Master, Depends(get_master_or_404)]


@router.post("", response_model=MasterRead, status_code=status.HTTP_201_CREATED)
async def create_master(data: MasterCreate, session: SessionDep) -> Master:
    master = Master(**data.model_dump())
    session.add(master)
    await commit_or_http_error(session)
    return master


@router.get("/{master_id}", response_model=MasterRead)
async def get_master(master: MasterDep) -> Master:
    return master


@router.get("", response_model=list[MasterRead])
async def list_masters(
    session: SessionDep,
    salon_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Sequence[Master]:
    stmt = select(Master)
    if salon_id is not None:
        stmt = stmt.where(Master.salon_id == salon_id)
    result = await session.scalars(stmt.order_by(Master.id).limit(limit))
    return result.all()


@router.patch("/{master_id}", response_model=MasterRead)
async def update_master(master: MasterDep, data: MasterUpdate, session: SessionDep) -> Master:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(master, field, value)
    await session.commit()
    return master
