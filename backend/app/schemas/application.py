import uuid

from pydantic import BaseModel, Field

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    care_request_id: uuid.UUID
    nurse_id: uuid.UUID
    message: str | None = Field(default=None, max_length=1000)


class ApplicationRejectRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    care_request_id: uuid.UUID
    nurse_id: uuid.UUID
    patient_id: uuid.UUID
    status: ApplicationStatus
    message: str | None
    rejection_reason: str | None

    model_config = {"from_attributes": True}
