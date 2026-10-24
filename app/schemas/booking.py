from datetime import datetime
from decimal import Decimal

from pydantic import AwareDatetime, BaseModel, ConfigDict, field_validator

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    master_id: int
    client_id: int
    service_id: int
    starts_at: AwareDatetime


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    master_id: int
    client_id: int
    service_id: int
    starts_at: datetime
    ends_at: datetime
    status: BookingStatus
    price_at_booking: Decimal
    created_at: datetime


class BookingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_at: AwareDatetime | None = None
    status: BookingStatus | None = None

    @field_validator("starts_at", "status")
    @classmethod
    def not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null")
        return value
