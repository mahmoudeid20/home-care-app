import uuid

from pydantic import BaseModel, Field


class LocationInput(BaseModel):
    governorate: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    area: str | None = Field(default=None, max_length=150)
    address_line: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class LocationResponse(LocationInput):
    id: uuid.UUID

    model_config = {"from_attributes": True}


class SpecialtyResponse(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    is_active: bool

    model_config = {"from_attributes": True}


class ServiceResponse(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    is_active: bool

    model_config = {"from_attributes": True}
