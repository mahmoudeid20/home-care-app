import uuid
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.care_request import CareRequestStatus, MobilityStatus
from app.models.nurse import Gender, PriceUnit, ShiftType
from app.schemas.lookup import LocationInput, LocationResponse, ServiceResponse, SpecialtyResponse


class CareRequestCreate(BaseModel):
    # --- Step 1: patient information ---
    patient_name: str = Field(min_length=2, max_length=150)
    patient_age: int = Field(ge=0, le=130)
    patient_gender: Gender
    medical_condition: str = Field(min_length=3, max_length=3000)
    mobility_status: MobilityStatus
    special_requirements: str | None = Field(default=None, max_length=2000)

    # --- Step 2: required care ---
    service_ids: list[uuid.UUID] = Field(min_length=1, description="At least one service is required")

    # --- Step 3: nurse requirements ---
    preferred_nurse_gender: Gender | None = None
    min_experience_years: int | None = Field(default=None, ge=0, le=70)
    required_specialty_ids: list[uuid.UUID] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    verified_nurses_only: bool = False
    preferred_shift: ShiftType = ShiftType.CUSTOM

    # --- Step 4: location ---
    location: LocationInput

    # --- Step 5: schedule ---
    start_date: date
    end_date: date | None = None
    hours_per_day: float | None = Field(default=None, gt=0, le=24)
    number_of_days: int | None = Field(default=None, gt=0)
    custom_schedule_note: str | None = Field(default=None, max_length=1000)
    payment_frequency: PriceUnit

    # --- Step 6: budget ---
    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date | None, info) -> date | None:
        start = info.data.get("start_date")
        if v is not None and start is not None and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v

    @model_validator(mode="after")
    def budget_range_valid(self) -> "CareRequestCreate":
        if self.budget_min is not None and self.budget_max is not None:
            if self.budget_min > self.budget_max:
                raise ValueError("budget_min must not exceed budget_max")
        return self


class CareRequestUpdate(BaseModel):
    """
    Partial update — only allowed while the request is still OPEN
    (enforced in the service layer, never trust the client here).
    """
    patient_name: str | None = Field(default=None, min_length=2, max_length=150)
    patient_age: int | None = Field(default=None, ge=0, le=130)
    patient_gender: Gender | None = None
    medical_condition: str | None = Field(default=None, min_length=3, max_length=3000)
    mobility_status: MobilityStatus | None = None
    special_requirements: str | None = Field(default=None, max_length=2000)

    service_ids: list[uuid.UUID] | None = None

    preferred_nurse_gender: Gender | None = None
    min_experience_years: int | None = Field(default=None, ge=0, le=70)
    required_specialty_ids: list[uuid.UUID] | None = None
    languages: list[str] | None = None
    verified_nurses_only: bool | None = None
    preferred_shift: ShiftType | None = None

    location: LocationInput | None = None

    start_date: date | None = None
    end_date: date | None = None
    hours_per_day: float | None = Field(default=None, gt=0, le=24)
    number_of_days: int | None = Field(default=None, gt=0)
    custom_schedule_note: str | None = Field(default=None, max_length=1000)
    payment_frequency: PriceUnit | None = None

    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)


class CareRequestResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    status: CareRequestStatus

    patient_name: str
    patient_age: int
    patient_gender: Gender
    medical_condition: str
    mobility_status: MobilityStatus
    special_requirements: str | None

    required_services: list[ServiceResponse] = Field(default_factory=list)

    preferred_nurse_gender: Gender | None
    min_experience_years: int | None
    required_specialties: list[SpecialtyResponse] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    verified_nurses_only: bool
    preferred_shift: ShiftType

    location: LocationResponse | None

    start_date: date
    end_date: date | None
    hours_per_day: float | None
    number_of_days: int | None
    custom_schedule_note: str | None
    payment_frequency: PriceUnit

    budget_min: float | None
    budget_max: float | None

    model_config = {"from_attributes": True}


def care_request_to_response(cr) -> "CareRequestResponse":
    """
    Manual construction, same rationale as nurse_to_response(): the
    required_services/required_specialties relationships are join-table
    rows, not Service/Specialty rows directly.
    """
    return CareRequestResponse(
        id=cr.id,
        patient_id=cr.patient_id,
        status=cr.status,
        patient_name=cr.patient_name,
        patient_age=cr.patient_age,
        patient_gender=cr.patient_gender,
        medical_condition=cr.medical_condition,
        mobility_status=cr.mobility_status,
        special_requirements=cr.special_requirements,
        required_services=[
            ServiceResponse.model_validate(rs.service) for rs in cr.required_services
        ],
        preferred_nurse_gender=cr.preferred_nurse_gender,
        min_experience_years=cr.min_experience_years,
        required_specialties=[
            SpecialtyResponse.model_validate(rs.specialty) for rs in cr.required_specialties
        ],
        languages=cr.languages or [],
        verified_nurses_only=cr.verified_nurses_only,
        preferred_shift=cr.preferred_shift,
        location=LocationResponse.model_validate(cr.location) if cr.location else None,
        start_date=cr.start_date,
        end_date=cr.end_date,
        hours_per_day=float(cr.hours_per_day) if cr.hours_per_day is not None else None,
        number_of_days=cr.number_of_days,
        custom_schedule_note=cr.custom_schedule_note,
        payment_frequency=cr.payment_frequency,
        budget_min=float(cr.budget_min) if cr.budget_min is not None else None,
        budget_max=float(cr.budget_max) if cr.budget_max is not None else None,
    )
