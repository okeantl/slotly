from pydantic import BaseModel, ConfigDict, Field, field_validator


class MasterCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    salon_id: int
    full_name: str = Field(min_length=1, max_length=200)


class MasterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    salon_id: int
    full_name: str


class MasterUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("full_name")
    @classmethod
    def not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null")
        return value
