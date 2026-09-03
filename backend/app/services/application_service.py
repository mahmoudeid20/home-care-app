"""
Application lifecycle (Section 17-18, 45): a patient sends a request to a
specific nurse; the nurse accepts or rejects it. Accepting an application
is the trigger that creates a Booking (Section 45's flow) — implemented
here rather than split across two services, since "accept application" and
"create booking" must happen atomically in one transaction.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.models.application import Application, ApplicationStatus
from app.models.booking import BookingStatus
from app.models.care_request import CareRequestStatus
from app.models.notification import NotificationType
from app.repositories.application_repository import ApplicationRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.care_request_repository import CareRequestRepository
from app.repositories.nurse_repository import NurseRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.application import ApplicationCreate
from app.services.notification_service import NotificationService


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.applications = ApplicationRepository(db)
        self.bookings = BookingRepository(db)
        self.care_requests = CareRequestRepository(db)
        self.patients = PatientRepository(db)
        self.nurses = NurseRepository(db)
        self.notifications = NotificationService(db)

    async def create(self, user_id: uuid.UUID, data: ApplicationCreate) -> Application:
        patient = await self.patients.get_by_user_id(user_id)
        if not patient:
            raise NotFoundError("You need a patient profile first")

        cr = await self.care_requests.get_by_id(data.care_request_id)
        if not cr or cr.patient_id != patient.id:
            raise NotFoundError("Care request not found")
        if cr.status != CareRequestStatus.OPEN:
            raise ValidationAppError(
                f"Care request is not open for new applications (status: {cr.status.value})"
            )

        nurse = await self.nurses.get_by_id(data.nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        if not nurse.is_approved or nurse.is_suspended:
            raise ValidationAppError("This nurse is not currently accepting requests")

        existing = await self.applications.get_active_for_nurse_and_request(cr.id, nurse.id)
        if existing:
            raise ConflictError("You already have a pending request to this nurse for this care request")

        app_ = await self.applications.create(
            care_request_id=cr.id, nurse_id=nurse.id, patient_id=patient.id, message=data.message
        )
        await self.notifications.notify(
            user_id=nurse.user_id,
            type_=NotificationType.NEW_REQUEST,
            title="New care request",
            body=f"{cr.patient_name} is looking for a nurse — you have a new request.",
            data={"application_id": str(app_.id), "care_request_id": str(cr.id)},
        )
        await self.db.commit()
        return app_

    async def _require_owned_by_nurse(self, user_id: uuid.UUID, application_id: uuid.UUID) -> Application:
        app_ = await self.applications.get_by_id(application_id)
        if not app_:
            raise NotFoundError("Application not found")
        nurse = await self.nurses.get_by_user_id(user_id)
        if not nurse or app_.nurse_id != nurse.id:
            raise ForbiddenError("You do not have access to this application")
        return app_

    async def _require_owned_by_patient(self, user_id: uuid.UUID, application_id: uuid.UUID) -> Application:
        app_ = await self.applications.get_by_id(application_id)
        if not app_:
            raise NotFoundError("Application not found")
        patient = await self.patients.get_by_user_id(user_id)
        if not patient or app_.patient_id != patient.id:
            raise ForbiddenError("You do not have access to this application")
        return app_

    async def accept(self, user_id: uuid.UUID, application_id: uuid.UUID):
        app_ = await self._require_owned_by_nurse(user_id, application_id)
        if app_.status != ApplicationStatus.PENDING:
            raise ValidationAppError(f"Application cannot be accepted (status: {app_.status.value})")

        cr = await self.care_requests.get_by_id(app_.care_request_id)
        if cr.status != CareRequestStatus.OPEN:
            raise ValidationAppError(
                f"Care request is no longer open (status: {cr.status.value})"
            )

        # Estimate the agreed price from the nurse's priced services that
        # match the request's payment frequency, same approach as the
        # matching engine's price scoring.
        nurse = await self.nurses.get_by_id(app_.nurse_id)
        required_service_ids = {rs.service_id for rs in cr.required_services}
        candidates = [
            ns for ns in nurse.services
            if ns.service_id in required_service_ids and ns.price_unit == cr.payment_frequency
        ]
        agreed_price = float(min(c.price for c in candidates)) if candidates else None

        await self.applications.set_status(app_, ApplicationStatus.ACCEPTED)

        booking = await self.bookings.create(
            care_request_id=cr.id,
            application_id=app_.id,
            patient_id=app_.patient_id,
            nurse_id=app_.nurse_id,
            status=BookingStatus.ACCEPTED,
            start_date=cr.start_date,
            end_date=cr.end_date,
            hours_per_day=cr.hours_per_day,
            payment_frequency=cr.payment_frequency,
            agreed_price=agreed_price,
        )

        await self.care_requests.set_status(cr, CareRequestStatus.MATCHED)

        # Auto-reject any other still-pending applications for this same
        # care request — the patient has effectively chosen this nurse.
        others = await self.applications.list_other_pending_for_request(cr.id, app_.id)
        for other in others:
            await self.applications.set_status(
                other, ApplicationStatus.REJECTED, rejection_reason="Another nurse was selected"
            )
            other_nurse = await self.nurses.get_by_id(other.nurse_id)
            await self.notifications.notify(
                user_id=other_nurse.user_id,
                type_=NotificationType.REQUEST_REJECTED,
                title="Request no longer available",
                body="The patient selected another nurse for this care request.",
                data={"application_id": str(other.id), "care_request_id": str(cr.id)},
            )

        patient = await self.patients.get_by_id(app_.patient_id)
        await self.notifications.notify(
            user_id=patient.user_id,
            type_=NotificationType.REQUEST_ACCEPTED,
            title="Your request was accepted",
            body=f"{nurse.full_name} accepted your care request.",
            data={"application_id": str(app_.id), "booking_id": str(booking.id)},
        )

        await self.db.commit()
        return app_, booking

    async def reject(self, user_id: uuid.UUID, application_id: uuid.UUID, reason: str | None):
        app_ = await self._require_owned_by_nurse(user_id, application_id)
        if app_.status != ApplicationStatus.PENDING:
            raise ValidationAppError(f"Application cannot be rejected (status: {app_.status.value})")
        await self.applications.set_status(app_, ApplicationStatus.REJECTED, rejection_reason=reason)

        patient = await self.patients.get_by_id(app_.patient_id)
        nurse = await self.nurses.get_by_id(app_.nurse_id)
        await self.notifications.notify(
            user_id=patient.user_id,
            type_=NotificationType.REQUEST_REJECTED,
            title="Request declined",
            body=f"{nurse.full_name} was unable to accept your care request.",
            data={"application_id": str(app_.id)},
        )

        await self.db.commit()
        return app_

    async def withdraw(self, user_id: uuid.UUID, application_id: uuid.UUID):
        app_ = await self._require_owned_by_patient(user_id, application_id)
        if app_.status != ApplicationStatus.PENDING:
            raise ValidationAppError(f"Application cannot be withdrawn (status: {app_.status.value})")
        await self.applications.set_status(app_, ApplicationStatus.WITHDRAWN)
        await self.db.commit()
        return app_

    async def list_received(self, user_id: uuid.UUID, limit: int = 20, offset: int = 0):
        nurse = await self.nurses.get_by_user_id(user_id)
        if not nurse:
            raise NotFoundError("You need a nurse profile first")
        return await self.applications.list_received_by_nurse(nurse.id, limit=limit, offset=offset)

    async def list_sent(self, user_id: uuid.UUID, limit: int = 20, offset: int = 0):
        patient = await self.patients.get_by_user_id(user_id)
        if not patient:
            raise NotFoundError("You need a patient profile first")
        return await self.applications.list_sent_by_patient(patient.id, limit=limit, offset=offset)
