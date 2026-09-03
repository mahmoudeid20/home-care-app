import uuid

from pydantic import BaseModel, Field, model_validator


class NurseMatchResult(BaseModel):
    """
    One ranked nurse recommendation for a care request (Section 21's
    example response shape, plus the marketplace card fields from
    Section 14 so the mobile app can render the result directly).
    """
    nurse_id: uuid.UUID
    full_name: str
    professional_title: str | None
    is_verified: bool = Field(
        description="True only if identity + qualification + experience are all admin-approved"
    )
    experience_years: int
    specialties: list[str] = Field(default_factory=list, description="Specialty names (English)")
    average_rating: float
    review_count: int
    governorate: str | None
    city: str | None

    match_score: float = Field(description="0-100 weighted match percentage")
    distance_km: float | None
    estimated_price: float | None
    payment_frequency: str | None
    matching_reasons: list[str] = Field(default_factory=list)


class MatchingWeightsResponse(BaseModel):
    skills_weight: float
    experience_weight: float
    location_weight: float
    availability_weight: float
    price_weight: float
    rating_weight: float
    verification_weight: float

    model_config = {"from_attributes": True}


class MatchingWeightsUpdate(BaseModel):
    skills_weight: float = Field(ge=0, le=1)
    experience_weight: float = Field(ge=0, le=1)
    location_weight: float = Field(ge=0, le=1)
    availability_weight: float = Field(ge=0, le=1)
    price_weight: float = Field(ge=0, le=1)
    rating_weight: float = Field(ge=0, le=1)
    verification_weight: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "MatchingWeightsUpdate":
        total = (
            self.skills_weight
            + self.experience_weight
            + self.location_weight
            + self.availability_weight
            + self.price_weight
            + self.rating_weight
            + self.verification_weight
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0 (100%), got {total:.3f}")
        return self
