"""
Payment lifecycle (Section 30-31). `create_for_booking` is called by
BookingService when a booking transitions to COMPLETED — computing the
commission split from the platform's configured percentage. Moving a
payment from PENDING to PAID is a deliberate, separate admin action
(cash/external tracking for the MVP); Section 30 explicitly forbids faking
a successful payment confirmation automatically.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.payment import Payment, PaymentStatus
from app.repositories.admin_action_repository import AdminActionRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.nurse_repository import NurseRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.platform_settings_repository import PlatformSettingsRepository


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.payments = PaymentRepository(db)
        self.bookings = BookingRepository(db)
        self.patients = PatientRepository(db)
        self.nurses = NurseRepository(db)
        self.settings = PlatformSettingsRepository(db)
        self.audit = AdminActionRepository(db)

    async def create_for_booking(self, booking) -> Payment | None:
        """
        Called from BookingService.complete(). Returns None (no-op) if the
        booking has no agreed_price — there's nothing to charge for (e.g.
        the matching engine couldn't price it — see
        MatchingService._price_score / ApplicationService.accept).
        """
        if booking.agreed_price is None:
            return None

        existing = await self.payments.get_by_booking_id(booking.id)
        if existing:
            return existing

        settings = await self.settings.get_active()
        commission_rate = float(settings.commission_percentage)
        amount = float(booking.agreed_price)
        commission = round(amount * commission_rate, 2)
        nurse_earnings = round(amount - commission, 2)

        return await self.payments.create(
            booking_id=booking.id,
            amount=amount,
            platform_commission=commission,
            nurse_earnings=nurse_earnings,
        )

    async def get_for_booking(self, user_id: uuid.UUID, booking_id: uuid.UUID) -> Payment:
        booking = await self.bookings.get_by_id(booking_id)
        if not booking:
            raise NotFoundError("Booking not found")

        patient = await self.patients.get_by_user_id(user_id)
        nurse = await self.nurses.get_by_user_id(user_id)
        is_owner = (patient and booking.patient_id == patient.id) or (
            nurse and booking.nurse_id == nurse.id
        )
        if not is_owner:
            raise ForbiddenError("You do not have access to this booking's payment")

        payment = await self.payments.get_by_booking_id(booking_id)
        if not payment:
            raise NotFoundError("No payment exists for this booking yet")
        return payment

    async def list_all(
        self, status: PaymentStatus | None = None, limit: int = 20, offset: int = 0
    ) -> list[Payment]:
        return await self.payments.list_all(status=status, limit=limit, offset=offset)

    async def mark_paid(
        self,
        admin_id: uuid.UUID,
        payment_id: uuid.UUID,
        payment_method: str,
        transaction_id: str | None,
    ) -> Payment:
        payment = await self.payments.get_by_id(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        if payment.status != PaymentStatus.PENDING:
            raise ValidationAppError(
                f"Only a PENDING payment can be marked paid (current status: {payment.status.value})"
            )
        await self.payments.set_status(
            payment, PaymentStatus.PAID, payment_method=payment_method, transaction_id=transaction_id
        )
        await self.audit.record(
            admin_id=admin_id, action_type="MARK_PAYMENT_PAID", target_type="payment", target_id=payment.id
        )
        await self.db.commit()
        return payment
