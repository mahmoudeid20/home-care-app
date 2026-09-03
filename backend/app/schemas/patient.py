import uuid

from pydantic import BaseModel, Field, field_validator

from app.schemas.lookup import LocationInput, LocationResponse
from app.utils.file_validation import validate_photo_url


class PatientCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    national_id: str | None = Field(default=None, min_length=14, max_length=14)
    preferred_language: str = Field(default="ar", pattern="^(ar|en)$")
    photo_url: str | None = Field(
        default=None,
        max_length=1024,
        description="URL of an already-uploaded profile photo in secure object storage.",
    )
    location: LocationInput | None = None

    validate_photo_url_ext = field_validator("photo_url")(validate_photo_url)


class PatientUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    national_id: str | None = Field(default=None, min_length=14, max_length=14)
    preferred_language: str | None = Field(default=None, pattern="^(ar|en)$")
    photo_url: str | None = Field(default=None, max_length=1024)
    location: LocationInput | None = None

    validate_photo_url_ext = field_validator("photo_url")(validate_photo_url)


class PatientResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    national_id: str | None = None
    preferred_language: str
    photo_url: str | None = None
    location: LocationResponse | None = None

    model_config = {"from_attributes": True}
