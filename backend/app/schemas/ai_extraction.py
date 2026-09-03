import uuid

from pydantic import BaseModel, Field


class AIExtractionRequest(BaseModel):
    text: str = Field(
        min_length=10,
        max_length=3000,
        description="Free-text description of the patient's situation and care needs.",
    )


class AIExtractionResult(BaseModel):
    """
    A pre-fill draft for the care request creation form (Section 22) --
    never auto-submitted. The patient reviews and edits this before
    calling POST /care-requests with the final values, exactly as if they
    had filled out the multi-step form by hand.
    """
    age: int | None = None
    gender: str | None = None
    patient_type: str | None = None
    duration_days: int | None = None
    hours_per_day: float | None = None
    preferred_shift: str | None = None
    languages: list[str] = Field(default_factory=list)
    mobility_status: str | None = None

    matched_specialty_ids: list[uuid.UUID] = Field(default_factory=list)
    unmatched_specialty_keywords: list[str] = Field(
        default_factory=list,
        description="Extracted specialty keywords that did not match any known specialty.",
    )
    matched_service_ids: list[uuid.UUID] = Field(default_factory=list)
    unmatched_service_keywords: list[str] = Field(
        default_factory=list,
        description="Extracted service keywords that did not match any known service.",
    )
