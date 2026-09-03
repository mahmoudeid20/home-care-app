"""
Chat models (Section 20): secure one-to-one messaging between a patient and
a nurse, persisted to PostgreSQL. A Conversation is created lazily the
first time either party reaches out (e.g. tapping "Message" on a nurse's
public profile, Section 16) — it doesn't require an existing booking,
though `booking_id` is set when the conversation originated from one.

The architecture leaves room for voice messages/calls and video calls
(Section 20: "prepared for... but do not implement in the first MVP")
by keeping MessageType open to extension without touching the Conversation
shape, and by not hard-coding assumptions about message content being
text-only anywhere in the schema.
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MessageType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    # VOICE / VIDEO_CALL_EVENT reserved for a future phase — not implemented
    # in this MVP (Section 20).


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("patient_id", "nurse_id", name="uq_conversation_patient_nurse"),
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nurse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )

    patient = relationship("Patient", foreign_keys=[patient_id])
    nurse = relationship("Nurse", foreign_keys=[nurse_id])
    booking = relationship("Booking", foreign_keys=[booking_id])
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, name="message_type"), default=MessageType.TEXT, nullable=False
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # created_at only (no updated_at) — messages are immutable once sent.
    # Uses a Python-side default (not server_default=func.now()) so we get
    # full microsecond precision consistently across backends — SQLite's
    # CURRENT_TIMESTAMP only has second resolution, which made two messages
    # sent within the same second sort non-deterministically.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
