from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionLocal


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def commit_or_http_error(session: AsyncSession) -> None:
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
