"""Platform-wide statistics for the admin dashboard (Section 27)."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.care_request import CareRequestService
from app.models.nurse import Nurse
from app.models.patient import Patient
from app.models.service import Service
from app.repositories.payment_repository import PaymentRepository
from app.schemas.admin import PlatformStatsResponse


class AdminStatsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payments = PaymentRepository(db)

    async def _count(self, stmt) -> int:
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_stats(self) -> PlatformStatsResponse:
        total_patients = await self._count(select(func.count()).select_from(Patient))
        total_nurses = await self._count(select(func.count()).select_from(Nurse))
        verified_nurses = await self._count(
            select(func.count()).select_from(Nurse).where(
                Nurse.identity_verified.is_(True),
                Nurse.qualification_verified.is_(True),
                Nurse.experience_verified.is_(True),
            )
        )
        pending_verifications = await self._count(
            select(func.count()).select_from(Nurse).where(
                (Nurse.identity_verified.is_(False))
                | (Nurse.qualification_verified.is_(False))
                | (Nurse.experience_verified.is_(False))
            )
        )

        active_statuses = [BookingStatus.ACCEPTED, BookingStatus.CONFIRMED, BookingStatus.ACTIVE]
        active_bookings = await self._count(
            select(func.count()).select_from(Booking).where(Booking.status.in_(active_statuses))
        )
        completed_bookings = await self._count(
            select(func.count()).select_from(Booking).where(
                Booking.status.in_([BookingStatus.COMPLETED, BookingStatus.REVIEWED])
            )
        )
        cancelled_bookings = await self._count(
            select(func.count()).select_from(Booking).where(Booking.status == BookingStatus.CANCELLED)
        )

        total_revenue = await self.payments.sum_paid_amount()
        platform_commission_earned = await self.payments.sum_paid_commission()

        avg_rating_result = await self.db.execute(
            select(func.coalesce(func.avg(Nurse.average_rating), 0)).where(Nurse.review_count > 0)
        )
        average_rating = round(float(avg_rating_result.scalar_one()), 2)

        most_requested_result = await self.db.execute(
            select(Service.name_en, func.count(CareRequestService.care_request_id).label("cnt"))
            .join(CareRequestService, CareRequestService.service_id == Service.id)
            .group_by(Service.name_en)
            .order_by(func.count(CareRequestService.care_request_id).desc())
            .limit(5)
        )
        most_requested_services = [
            {"service": row[0], "count": row[1]} for row in most_requested_result.all()
        ]

        return PlatformStatsResponse(
            total_patients=total_patients,
            total_nurses=total_nurses,
            verified_nurses=verified_nurses,
            pending_verifications=pending_verifications,
            active_bookings=active_bookings,
            completed_bookings=completed_bookings,
            cancelled_bookings=cancelled_bookings,
            total_revenue=total_revenue,
            platform_commission_earned=platform_commission_earned,
            average_rating=average_rating,
            most_requested_services=most_requested_services,
        )
