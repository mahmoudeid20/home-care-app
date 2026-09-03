"""
Booking state machine (Section 19). Every transition is validated here
against an explicit allowed-transitions map — the mobile client sends an
action (confirm/start/complete/cancel), never a raw status value, and the
server alone decides whether the transition is legal from the current
state and who is allowed to trigger it.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.booking import Booking, BookingStatus
from app.models.care_request import CareRequestStatus
from app.models.notification import NotificationType
from app.repositories.booking_repository import BookingRepository
from app.repositories.care_request_repository import CareRequestRepository
from app.repositories.nurse_repository import NurseRepository
from app.repositories.patient_repository import PatientRepository
from app.services.notification_service import NotificationService
from app.services.payment_service import PaymentService

# Which actor ("patient" / "nurse") may trigger which status transition.
_TRANSITIONS: dict[BookingStatus, dict[BookingStatus, set[str]]] = {
    BookingStatus.ACCEPTED: {
        BookingStatus.CONFIRMED: {"patient"},
        BookingStatus.CANCELLED: {"patient", "nurse"},
    },
    BookingStatus.CONFIRMED: {
        BookingStatus.ACTIVE: {"nurse"},
        BookingStatus.CANCELLED: {"patient", "nurse"},
    },
    BookingStatus.ACTIVE: {
        BookingStatus.COMPLETED: {"nurse"},
    },
    # COMPLETED -> REVIEWED is set by the review service (Phase 7) when a
    # review is submitted, never via a direct client action.
}


class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bookings = BookingRepository(db)
        self.care_requests = CareRequestRepository(db)
        self.patients = PatientRepository(db)
        self.nurses = NurseRepository(db)
        self.notifications = NotificationService(db)
        self.payments = PaymentService(db)

    async def _get_with_role(self, user_id: uuid.UUID, booking_id: uuid.UUID) -> tuple[Booking, str]:
        booking = await self.bookings.get_by_id(booking_id)
        if not booking:
            raise NotFoundError("Booking not found")

        patient = await self.patients.get_by_user_id(user_id)
        if patient and booking.patient_id == patient.id:
            return booking, "patient"

        nurse = await self.nurses.get_by_user_id(user_id)
        if nurse and booking.nurse_id == nurse.id:
            return booking, "nurse"

        raise ForbiddenError("You do not have access to this booking")

    async def _transition(
        self, user_id: uuid.UUID, booking_id: uuid.UUID, target: BookingStatus
    ) -> Booking:
        booking, role = await self._get_with_role(user_id, booking_id)

        allowed_targets = _TRANSITIONS.get(booking.status, {})
        allowed_roles = allowed_targets.get(target)
        if allowed_roles is None:
            raise ValidationAppError(
                f"Cannot move booking from {booking.status.value} to {target.value}"
            )
        if role not in allowed_roles:
            raise ForbiddenError(f"Only {'/'.join(sorted(allowed_roles))} can perform this action")

        await self.bookings.set_status(booking, target)

        if target == BookingStatus.CANCELLED:
            # Free up the care request so the patient can look for another
            # nurse, unless it's already in some other terminal state.
            cr = await self.care_requests.get_by_id(booking.care_request_id)
            if cr and cr.status == CareRequestStatus.MATCHED:
                await self.care_requests.set_status(cr, CareRequestStatus.OPEN)

        await self._notify_transition(booking, target, triggered_by_role=role)

        if target == BookingStatus.COMPLETED:
            await self.payments.create_for_booking(booking)

        await self.db.commit()
        return booking

    async def _notify_transition(
        self, booking: Booking, target: BookingStatus, triggered_by_role: str
    ) -> None:
        """Section 25's trigger list: 'Booking confirmed' and 'Booking
        cancelled'. Notifies the *other* party — not the one who triggered
        the action, since they already know they just did it."""
        patient = await self.patients.get_by_id(booking.patient_id)
        nurse = await self.nurses.get_by_id(booking.nurse_id)

        if target == BookingStatus.CONFIRMED:
            await self.notifications.notify(
                user_id=nurse.user_id,
                type_=NotificationType.BOOKING_CONFIRMED,
                title="Booking confirmed",
                body=f"{patient.full_name} confirmed the booking.",
                data={"booking_id": str(booking.id)},
            )
        elif target == BookingStatus.CANCELLED:
            recipient = nurse.user_id if triggered_by_role == "patient" else patient.user_id
            other_name = patient.full_name if triggered_by_role == "patient" else nurse.full_name
            await self.notifications.notify(
                user_id=recipient,
                type_=NotificationType.BOOKING_CANCELLED,
                title="Booking cancelled",
                body=f"{other_name} cancelled the booking.",
                data={"booking_id": str(booking.id)},
            )


    async def confirm(self, user_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
        return await self._transition(user_id, booking_id, BookingStatus.CONFIRMED)

    async def start(self, user_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
        return await self._transition(user_id, booking_id, BookingStatus.ACTIVE)

    async def complete(self, user_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
        return await self._transition(user_id, booking_id, BookingStatus.COMPLETED)

    async def cancel(self, user_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
        return await self._transition(user_id, booking_id, BookingStatus.CANCELLED)

    async def get(self, user_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
        booking, _role = await self._get_with_role(user_id, booking_id)
        return booking

    async def list_mine(self, user_id: uuid.UUID, limit: int = 20, offset: int = 0) -> list[Booking]:
        patient = await self.patients.get_by_user_id(user_id)
        if patient:
            return await self.bookings.list_for_patient(patient.id, limit=limit, offset=offset)
        nurse = await self.nurses.get_by_user_id(user_id)
        if nurse:
            return await self.bookings.list_for_nurse(nurse.id, limit=limit, offset=offset)
        return []
