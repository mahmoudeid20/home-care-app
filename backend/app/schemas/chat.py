import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.conversation import MessageType
from app.utils.file_validation import (
    ALLOWED_GENERIC_FILE_EXTENSIONS,
    ALLOWED_IMAGE_EXTENSIONS,
    is_allowed_extension,
)


class ConversationCreate(BaseModel):
    nurse_id: uuid.UUID


class ConversationResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    nurse_id: uuid.UUID
    booking_id: uuid.UUID | None
    other_party_name: str = Field(
        description="The nurse's name (if viewed by the patient) or vice versa"
    )
    last_message_preview: str | None = None
    last_message_at: datetime | None = None

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    message_type: MessageType = MessageType.TEXT
    content: str | None = Field(default=None, max_length=5000)
    attachment_url: str | None = Field(default=None, max_length=1024)

    @model_validator(mode="after")
    def content_or_attachment_required(self) -> "MessageCreate":
        if self.message_type == MessageType.TEXT:
            if not self.content or not self.content.strip():
                raise ValueError("content is required for TEXT messages")
        else:
            if not self.attachment_url:
                raise ValueError("attachment_url is required for IMAGE/FILE messages")
            allowed = (
                ALLOWED_IMAGE_EXTENSIONS
                if self.message_type == MessageType.IMAGE
                else ALLOWED_GENERIC_FILE_EXTENSIONS
            )
            if not is_allowed_extension(self.attachment_url, allowed):
                raise ValueError(
                    f"Unsupported attachment type for {self.message_type.value}. "
                    f"Allowed: {', '.join(sorted(allowed))}"
                )
        return self


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    message_type: MessageType
    content: str | None
    attachment_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
