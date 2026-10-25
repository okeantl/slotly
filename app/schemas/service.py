from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ServiceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    salon_id: int
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    duration_minutes: int = Field(gt=0, le=480)


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    salon_id: int
    name: str
    price: Decimal
    duration_minutes: int


class ServiceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    duration_minutes: int | None = Field(default=None, gt=0, le=480)

    @field_validator("name", "price", "duration_minutes")
    @classmethod
    def not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null")
        return value
