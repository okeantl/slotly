from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SalonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    timezone: str = "Europe/Moscow"


class SalonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    timezone: str
    created_at: datetime


class SalonUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = None

    @field_validator("name", "timezone")
    @classmethod
    def not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null")
        return value
