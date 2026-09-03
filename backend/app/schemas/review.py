import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    booking_id: uuid.UUID
    overall_rating: int = Field(ge=1, le=5)
    professionalism: int = Field(ge=1, le=5)
    communication: int = Field(ge=1, le=5)
    care_quality: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    patient_id: uuid.UUID
    nurse_id: uuid.UUID
    overall_rating: int
    professionalism: int
    communication: int
    care_quality: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
