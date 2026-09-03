import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.complaint import ComplaintStatus


class ComplaintCreate(BaseModel):
    booking_id: uuid.UUID | None = None
    category: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=3000)
    attachments: list[str] = Field(
        default_factory=list, description="URLs of already-uploaded files"
    )


class ComplaintAdminUpdate(BaseModel):
    status: ComplaintStatus
    admin_response: str | None = Field(default=None, max_length=3000)


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    booking_id: uuid.UUID | None
    category: str
    description: str
    attachments: list[str] = Field(default_factory=list)
    status: ComplaintStatus
    admin_response: str | None
    created_at: datetime

    @field_validator("attachments", mode="before")
    @classmethod
    def none_to_empty_list(cls, v):
        return v if v is not None else []

    model_config = {"from_attributes": True}
