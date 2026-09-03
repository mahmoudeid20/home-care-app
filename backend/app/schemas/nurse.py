import uuid
from datetime import date, time

from pydantic import BaseModel, Field, field_validator

from app.models.nurse import DocumentStatus, DocumentType, Gender, PriceUnit, ShiftType
from app.schemas.lookup import LocationInput, LocationResponse, ServiceResponse, SpecialtyResponse
from app.utils.file_validation import (
    ALLOWED_DOCUMENT_EXTENSIONS,
    is_allowed_extension,
    validate_photo_url,
)


class NurseServiceInput(BaseModel):
    service_id: uuid.UUID
    price: float = Field(gt=0, description="Numeric price, never a formatted string (Section 13)")
    price_unit: PriceUnit


class NurseAvailabilityInput(BaseModel):
    day_of_week: int | None = Field(default=None, ge=0, le=6, description="0=Monday ... 6=Sunday")
    shift_type: ShiftType
    start_time: time | None = None
    end_time: time | None = None

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: time | None, info) -> time | None:
        start = info.data.get("start_time")
        if v is not None and start is not None and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class NurseCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    professional_title: str | None = Field(default=None, max_length=150)
    bio: str | None = Field(default=None, max_length=2000)
    gender: Gender
    date_of_birth: date | None = None
    experience_years: int = Field(default=0, ge=0, le=70)
    education: str | None = Field(default=None, max_length=2000)
    photo_url: str | None = Field(
        default=None,
        max_length=1024,
        description="URL of an already-uploaded profile photo in secure object storage.",
    )

    location: LocationInput | None = None
    specialty_ids: list[uuid.UUID] = Field(default_factory=list)
    services: list[NurseServiceInput] = Field(default_factory=list)
    availability: list[NurseAvailabilityInput] = Field(default_factory=list)

    validate_photo_url_ext = field_validator("photo_url")(validate_photo_url)


class NurseUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    professional_title: str | None = Field(default=None, max_length=150)
    bio: str | None = Field(default=None, max_length=2000)
    experience_years: int | None = Field(default=None, ge=0, le=70)
    education: str | None = Field(default=None, max_length=2000)
    photo_url: str | None = Field(default=None, max_length=1024)
    location: LocationInput | None = None
    specialty_ids: list[uuid.UUID] | None = None
    services: list[NurseServiceInput] | None = None
    availability: list[NurseAvailabilityInput] | None = None

    validate_photo_url_ext = field_validator("photo_url")(validate_photo_url)


class NurseAvailabilityResponse(BaseModel):
    id: uuid.UUID
    day_of_week: int | None
    shift_type: ShiftType
    start_time: time | None
    end_time: time | None

    model_config = {"from_attributes": True}


class NurseServiceResponse(BaseModel):
    service: ServiceResponse
    price: float
    price_unit: PriceUnit

    model_config = {"from_attributes": True}


class NurseResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    professional_title: str | None
    bio: str | None
    gender: Gender
    experience_years: int
    education: str | None
    photo_url: str | None = None
    location: LocationResponse | None = None

    identity_verified: bool
    qualification_verified: bool
    experience_verified: bool
    is_approved: bool
    is_suspended: bool

    average_rating: float
    review_count: int

    specialties: list[SpecialtyResponse] = Field(default_factory=list)
    services: list[NurseServiceResponse] = Field(default_factory=list)
    availability: list[NurseAvailabilityResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


def nurse_to_response(nurse) -> "NurseResponse":
    """
    Build a NurseResponse from an ORM Nurse instance.

    Manual construction (rather than NurseResponse.model_validate(nurse))
    is required because `nurse.specialties` is a list of the join-table rows
    (NurseSpecialty), not Specialty rows — Pydantic's automatic
    from_attributes traversal can't bridge that extra hop, so we unwrap the
    nested `.specialty` / `.service` relationship explicitly here.
    """
    return NurseResponse(
        id=nurse.id,
        user_id=nurse.user_id,
        full_name=nurse.full_name,
        professional_title=nurse.professional_title,
        bio=nurse.bio,
        gender=nurse.gender,
        experience_years=nurse.experience_years,
        education=nurse.education,
        photo_url=nurse.photo_url,
        location=LocationResponse.model_validate(nurse.location) if nurse.location else None,
        identity_verified=nurse.identity_verified,
        qualification_verified=nurse.qualification_verified,
        experience_verified=nurse.experience_verified,
        is_approved=nurse.is_approved,
        is_suspended=nurse.is_suspended,
        average_rating=float(nurse.average_rating),
        review_count=nurse.review_count,
        specialties=[
            SpecialtyResponse.model_validate(ns.specialty) for ns in nurse.specialties
        ],
        services=[
            NurseServiceResponse(
                service=ServiceResponse.model_validate(ns.service),
                price=float(ns.price),
                price_unit=ns.price_unit,
            )
            for ns in nurse.services
        ],
        availability=[
            NurseAvailabilityResponse.model_validate(a) for a in nurse.availability_slots
        ],
    )


class NurseSearchResult(BaseModel):
    """Marketplace card (Section 14) — lean summary for list/browse views."""
    id: uuid.UUID
    full_name: str
    professional_title: str | None
    photo_url: str | None = None
    is_verified: bool
    experience_years: int
    specialties: list[str] = Field(default_factory=list)
    average_rating: float
    review_count: int
    governorate: str | None
    city: str | None
    starting_price: float | None = Field(
        default=None, description="Lowest listed price across the nurse's services"
    )
    price_unit: PriceUnit | None = None

    model_config = {"from_attributes": True}


def nurse_to_search_result(nurse) -> "NurseSearchResult":
    prices = [(ns.price, ns.price_unit) for ns in nurse.services]
    starting = min(prices, key=lambda p: p[0]) if prices else (None, None)
    return NurseSearchResult(
        id=nurse.id,
        full_name=nurse.full_name,
        professional_title=nurse.professional_title,
        photo_url=nurse.photo_url,
        is_verified=nurse.is_fully_verified,
        experience_years=nurse.experience_years,
        specialties=[ns.specialty.name_en for ns in nurse.specialties],
        average_rating=float(nurse.average_rating),
        review_count=nurse.review_count,
        governorate=nurse.location.governorate if nurse.location else None,
        city=nurse.location.city if nurse.location else None,
        starting_price=float(starting[0]) if starting[0] is not None else None,
        price_unit=starting[1],
    )


class NurseDocumentUploadRequest(BaseModel):
    document_type: DocumentType
    file_url: str = Field(
        min_length=1,
        max_length=1024,
        description="URL of the already-uploaded file in secure object storage.",
    )

    @field_validator("file_url")
    @classmethod
    def validate_extension(cls, v: str) -> str:
        if not is_allowed_extension(v, ALLOWED_DOCUMENT_EXTENSIONS):
            raise ValueError(
                f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))}"
            )
        return v


class NurseDocumentResponse(BaseModel):
    id: uuid.UUID
    document_type: DocumentType
    status: DocumentStatus
    rejection_reason: str | None

    model_config = {"from_attributes": True}
