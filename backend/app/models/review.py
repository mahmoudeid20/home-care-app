"""
A Review can only be created once, tied to exactly one COMPLETED booking
(Section 24: "Only allow a patient to review a nurse after a completed
booking" / "Prevent duplicate reviews for the same completed booking").
The unique constraint on booking_id is the hard backstop; ReviewService
also checks the booking's status transitions to REVIEWED, which itself
prevents a second review attempt at the service layer.
"""
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

_RATING_RANGE = CheckConstraint(
    "overall_rating BETWEEN 1 AND 5 AND professionalism BETWEEN 1 AND 5 "
    "AND communication BETWEEN 1 AND 5 AND care_quality BETWEEN 1 AND 5",
    name="ck_review_ratings_1_to_5",
)


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (_RATING_RANGE,)

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nurse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    professionalism: Mapped[int] = mapped_column(Integer, nullable=False)
    communication: Mapped[int] = mapped_column(Integer, nullable=False)
    care_quality: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    booking = relationship("Booking", foreign_keys=[booking_id])
    patient = relationship("Patient", foreign_keys=[patient_id])
    nurse = relationship("Nurse", foreign_keys=[nurse_id])
