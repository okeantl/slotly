import asyncio

from pydantic import ValidationError

from app.core.db import SessionLocal, engine
from app.models import Booking
from app.schemas.booking import BookingCreate, BookingRead


async def main() -> None:
    print(
        BookingCreate.model_validate(
            {
                "master_id": "2",
                "client_id": 2,
                "service_id": 1,
                "starts_at": "2026-10-25T10:00+03:00",
            }
        )
    )

    for bad in (
        {
            "master_id": "abc",
            "client_id": 2,
            "service_id": 1,
            "starts_at": "2026-10-25T10:00+03:00",
        },
        {"master_id": 2, "client_id": 2, "service_id": 1, "starts_at": "2026-10-25T10:00"},
        {
            "master_id": 2,
            "client_id": 2,
            "service_id": 1,
            "starts_at": "2026-10-25T10:00+03:00",
            "price_at_booking": 1,
        },
    ):
        try:
            BookingCreate.model_validate(bad)
        except ValidationError as exc:
            print(exc.errors()[0]["type"], exc.errors()[0]["loc"])

    async with SessionLocal() as session:
        booking = await session.get(Booking, 1)
        assert booking is not None
        print(BookingRead.model_validate(booking).model_dump_json(indent=2))
    await engine.dispose()


asyncio.run(main())
