"""
Payment record (Section 30). Created automatically in PENDING status when
a booking is marked COMPLETED (BookingService.complete), with the
commission split computed from the platform's configured percentage
(Section 31). For the MVP, moving PENDING -> PAID is a manual admin action
(cash/external payment tracking) - Section 30: "Do not implement fake
successful payment confirmations in production." Real gateway integration
would add a webhook that calls the same PaymentService.mark_paid path.
"""
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class Payment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "payments"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EGP", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    platform_commission: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    nurse_earnings: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    booking = relationship("Booking", foreign_keys=[booking_id])
