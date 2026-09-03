"""
Review creation (Section 24). On success this does four things atomically:
  1. Persists the Review row (unique per booking_id - duplicate backstop)
  2. Recomputes the nurse's denormalized average_rating/review_count
     (used everywhere else - search, matching, public profile - so those
     stay fast without a JOIN/AVG() on every read)
  3. Transitions the booking COMPLETED -> REVIEWED, closing the state
     machine loop from Phase 5 (Section 19)
  4. Notifies the nurse (Section 25: "New review")
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.models.booking import BookingStatus
from app.models.notification import NotificationType
from app.models.review import Review
from app.repositories.booking_repository import BookingRepository
from app.repositories.nurse_repository import NurseRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate
from app.services.notification_service import NotificationService


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.reviews = ReviewRepository(db)
        self.bookings = BookingRepository(db)
        self.patients = PatientRepository(db)
        self.nurses = NurseRepository(db)
        self.notifications = NotificationService(db)

    async def create(self, user_id: uuid.UUID, data: ReviewCreate) -> Review:
        patient = await self.patients.get_by_user_id(user_id)
        if not patient:
            raise NotFoundError("You need a patient profile first")

        booking = await self.bookings.get_by_id(data.booking_id)
        if not booking:
            raise NotFoundError("Booking not found")
        if booking.patient_id != patient.id:
            raise ForbiddenError("You do not have access to this booking")

        # Check for a duplicate review before the status check: once a
        # booking has been reviewed its status is REVIEWED (no longer
        # COMPLETED), so checking status first would misreport a repeat
        # attempt as "not completed yet" (422) instead of the more precise
        # "already reviewed" (409).
        if await self.reviews.get_by_booking_id(booking.id):
            raise ConflictError("This booking has already been reviewed")

        if booking.status != BookingStatus.COMPLETED:
            raise ValidationAppError(
                f"Can only review a COMPLETED booking (current status: {booking.status.value})"
            )

        review = await self.reviews.create(
            booking_id=booking.id,
            patient_id=patient.id,
            nurse_id=booking.nurse_id,
            overall_rating=data.overall_rating,
            professionalism=data.professionalism,
            communication=data.communication,
            care_quality=data.care_quality,
            comment=data.comment,
        )

        nurse = await self.nurses.get_by_id(booking.nurse_id)
        new_count = nurse.review_count + 1
        new_avg = (float(nurse.average_rating) * nurse.review_count + data.overall_rating) / new_count
        nurse.review_count = new_count
        nurse.average_rating = round(new_avg, 2)

        await self.bookings.set_status(booking, BookingStatus.REVIEWED)

        await self.notifications.notify(
            user_id=nurse.user_id,
            type_=NotificationType.NEW_REVIEW,
            title="New review received",
            body=f"You received a {data.overall_rating}-star review.",
            data={"booking_id": str(booking.id), "review_id": str(review.id)},
        )

        await self.db.commit()
        return review

    async def list_for_nurse(self, nurse_id: uuid.UUID, limit: int = 20, offset: int = 0):
        return await self.reviews.list_for_nurse(nurse_id, limit=limit, offset=offset)
