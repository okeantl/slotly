from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import SessionDep, commit_or_http_error
from app.models import Service
from app.schemas.service import ServiceCreate, ServiceRead, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


async def get_service_or_404(service_id: int, session: SessionDep) -> Service:
    service = await session.get(Service, service_id)
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "service not found")
    return service


ServiceDep = Annotated[Service, Depends(get_service_or_404)]


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(data: ServiceCreate, session: SessionDep) -> Service:
    service = Service(**data.model_dump())
    session.add(service)
    await commit_or_http_error(session)
    return service


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(service: ServiceDep) -> Service:
    return service


@router.get("", response_model=list[ServiceRead])
async def list_services(
    session: SessionDep,
    salon_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Sequence[Service]:
    stmt = select(Service)
    if salon_id is not None:
        stmt = stmt.where(Service.salon_id == salon_id)
    result = await session.scalars(stmt.order_by(Service.id).limit(limit))
    return result.all()


@router.patch("/{service_id}", response_model=ServiceRead)
async def update_service(service: ServiceDep, data: ServiceUpdate, session: SessionDep) -> Service:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(service, field, value)
    await session.commit()
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service: ServiceDep, session: SessionDep) -> None:
    await session.delete(service)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if getattr(exc.orig, "sqlstate", None) == "23503":
            raise HTTPException(status.HTTP_409_CONFLICT, "service has bookings") from exc
        raise
