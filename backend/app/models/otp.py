import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class OTPChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"


class OTPPurpose(str, enum.Enum):
    REGISTRATION = "REGISTRATION"
    LOGIN = "LOGIN"
    PASSWORD_RESET = "PASSWORD_RESET"


class OTPCode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "otp_codes"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    recipient: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    channel: Mapped[OTPChannel] = mapped_column(
        Enum(OTPChannel, name="otp_channel"), nullable=False, default=OTPChannel.EMAIL
    )
    purpose: Mapped[OTPPurpose] = mapped_column(
        Enum(OTPPurpose, name="otp_purpose"), nullable=False, default=OTPPurpose.REGISTRATION
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user = relationship("User", foreign_keys=[user_id])

    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp
