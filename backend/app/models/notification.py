"""
Notification records (Section 25). Every push notification also gets a
persisted row here so the mobile app has an in-app notification center,
not just a transient push -- and so delivery can be retried/audited even
if FCM delivery itself fails or the device is offline.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class NotificationType(str, enum.Enum):
    NEW_REQUEST = "NEW_REQUEST"
    REQUEST_ACCEPTED = "REQUEST_ACCEPTED"
    REQUEST_REJECTED = "REQUEST_REJECTED"
    BOOKING_CONFIRMED = "BOOKING_CONFIRMED"
    BOOKING_CANCELLED = "BOOKING_CANCELLED"
    NEW_MESSAGE = "NEW_MESSAGE"
    BOOKING_REMINDER = "BOOKING_REMINDER"
    DOCUMENT_VERIFICATION_RESULT = "DOCUMENT_VERIFICATION_RESULT"
    NEW_REVIEW = "NEW_REVIEW"


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # Arbitrary structured payload for deep-linking (e.g. {"booking_id": "..."}).
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
