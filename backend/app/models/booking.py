"""
A Booking is created the moment a nurse accepts an application (Section 45:
"nurse accepts -> booking is created"). Its status starts at ACCEPTED
(the "nurse accepted" step already happened via the Application) and then
follows Section 19's lifecycle:

    ACCEPTED -> CONFIRMED -> ACTIVE -> COMPLETED -> REVIEWED
                    \\-> CANCELLED        \\-> CANCELLED

All transitions are validated server-side in BookingService — the mobile
client can never set status directly (Section 19: "Never trust the mobile
client to control booking status").
"""
import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.nurse import PriceUnit


class BookingStatus(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    CONFIRMED = "CONFIRMED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    REVIEWED = "REVIEWED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Booking(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bookings"

    care_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nurse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.ACCEPTED,
        nullable=False,
        index=True,
    )

    # Snapshotted from the care request at booking-creation time so later
    # edits to the (now-closed) care request never retroactively change an
    # active booking's terms.
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    hours_per_day: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    payment_frequency: Mapped[PriceUnit] = mapped_column(Enum(PriceUnit, name="price_unit"), nullable=False)
    # Numeric only, never a formatted string (Section 13). Nullable because
    # a price match isn't always available (see MatchingService._price_score).
    agreed_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    care_request = relationship("CareRequest", foreign_keys=[care_request_id])
    application = relationship("Application", foreign_keys=[application_id])
    patient = relationship("Patient", foreign_keys=[patient_id])
    nurse = relationship("Nurse", foreign_keys=[nurse_id])
