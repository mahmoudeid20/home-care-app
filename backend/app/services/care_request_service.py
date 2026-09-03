import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.care_request import CareRequest, CareRequestStatus
from app.repositories.care_request_repository import CareRequestRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.lookup_repository import LookupRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.nurse_repository import NurseRepository
from app.repositories.application_repository import ApplicationRepository
from app.schemas.care_request import CareRequestCreate, CareRequestUpdate

# Status transitions a patient is allowed to trigger directly. MATCHED is
# set by the booking service (Phase 5) when a booking is confirmed, never
# directly by the patient — so it's deliberately excluded here.
_CANCELLABLE_STATUSES = {CareRequestStatus.OPEN, CareRequestStatus.MATCHED}
_EDITABLE_STATUSES = {CareRequestStatus.OPEN}


class CareRequestService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.care_requests = CareRequestRepository(db)
        self.patients = PatientRepository(db)
        self.locations = LocationRepository(db)
        self.lookup = LookupRepository(db)
        self.nurses = NurseRepository(db)
        self.applications = ApplicationRepository(db)

    async def _require_patient_profile(self, user_id: uuid.UUID):
        patient = await self.patients.get_by_user_id(user_id)
        if not patient:
            raise NotFoundError(
                "You need a patient profile before creating a care request. "
                "Create one via POST /patients/me first."
            )
        return patient

    async def _validate_service_ids(self, service_ids: list[uuid.UUID]) -> None:
        valid = {s.id for s in await self.lookup.list_services(active_only=False)}
        unknown = set(service_ids) - valid
        if unknown:
            raise ValidationAppError(f"Unknown service id(s): {sorted(str(u) for u in unknown)}")

    async def _validate_specialty_ids(self, specialty_ids: list[uuid.UUID]) -> None:
        if not specialty_ids:
            return
        valid = {s.id for s in await self.lookup.list_specialties(active_only=False)}
        unknown = set(specialty_ids) - valid
        if unknown:
            raise ValidationAppError(f"Unknown specialty id(s): {sorted(str(u) for u in unknown)}")

    async def _get_owned(self, user_id: uuid.UUID, care_request_id: uuid.UUID) -> CareRequest:
        cr = await self.care_requests.get_by_id(care_request_id)
        if not cr:
            raise NotFoundError("Care request not found")
        patient = await self.patients.get_by_user_id(user_id)
        if not patient or cr.patient_id != patient.id:
            raise ForbiddenError("You do not have access to this care request")
        return cr

    async def create(self, user_id: uuid.UUID, data: CareRequestCreate) -> CareRequest:
        patient = await self._require_patient_profile(user_id)

        await self._validate_service_ids(data.service_ids)
        await self._validate_specialty_ids(data.required_specialty_ids)

        location = await self.locations.create(data.location)

        cr = await self.care_requests.create(
            patient_id=patient.id,
            status=CareRequestStatus.OPEN,
            patient_name=data.patient_name,
            patient_age=data.patient_age,
            patient_gender=data.patient_gender,
            medical_condition=data.medical_condition,
            mobility_status=data.mobility_status,
            special_requirements=data.special_requirements,
            preferred_nurse_gender=data.preferred_nurse_gender,
            min_experience_years=data.min_experience_years,
            languages=data.languages,
            verified_nurses_only=data.verified_nurses_only,
            preferred_shift=data.preferred_shift,
            location_id=location.id,
            start_date=data.start_date,
            end_date=data.end_date,
            hours_per_day=data.hours_per_day,
            number_of_days=data.number_of_days,
            custom_schedule_note=data.custom_schedule_note,
            payment_frequency=data.payment_frequency,
            budget_min=data.budget_min,
            budget_max=data.budget_max,
        )

        await self.care_requests.replace_services(cr, data.service_ids)
        if data.required_specialty_ids:
            await self.care_requests.replace_specialties(cr, data.required_specialty_ids)

        await self.db.commit()
        return await self.care_requests.get_by_id(cr.id)

    async def get(self, user_id: uuid.UUID, care_request_id: uuid.UUID) -> CareRequest:
        """Read access, not just the owning patient: a nurse who has
        applied to this care request (any application status — pending,
        accepted, rejected, or withdrawn) can view it too, matching
        Section 18's "New Requests" nurse view — they need to see what
        they're being asked to do before accepting/rejecting. Editing and
        cancelling stay patient-only via _get_owned below."""
        cr = await self.care_requests.get_by_id(care_request_id)
        if not cr:
            raise NotFoundError("Care request not found")

        patient = await self.patients.get_by_user_id(user_id)
        if patient and cr.patient_id == patient.id:
            return cr

        nurse = await self.nurses.get_by_user_id(user_id)
        if nurse:
            application = await self.applications.get_any_for_nurse_and_request(cr.id, nurse.id)
            if application:
                return cr

        raise ForbiddenError("You do not have access to this care request")

    async def list_mine(self, user_id: uuid.UUID, limit: int = 20, offset: int = 0) -> list[CareRequest]:
        patient = await self._require_patient_profile(user_id)
        return await self.care_requests.list_by_patient(patient.id, limit=limit, offset=offset)

    async def update(
        self, user_id: uuid.UUID, care_request_id: uuid.UUID, data: CareRequestUpdate
    ) -> CareRequest:
        cr = await self._get_owned(user_id, care_request_id)
        if cr.status not in _EDITABLE_STATUSES:
            raise ValidationAppError(
                f"Care request cannot be edited while status is {cr.status.value}"
            )

        if data.service_ids is not None:
            await self._validate_service_ids(data.service_ids)
        if data.required_specialty_ids is not None:
            await self._validate_specialty_ids(data.required_specialty_ids)

        simple_fields = data.model_dump(
            exclude_unset=True,
            exclude={"service_ids", "required_specialty_ids", "location"},
        )
        for field, value in simple_fields.items():
            setattr(cr, field, value)

        if data.location is not None:
            if cr.location_id:
                existing = await self.locations.get_by_id(cr.location_id)
                await self.locations.update(existing, data.location)
                cr.location = existing  # keep relationship in sync, see PatientService
            else:
                new_location = await self.locations.create(data.location)
                cr.location_id = new_location.id
                cr.location = new_location

        if data.service_ids is not None:
            await self.care_requests.replace_services(cr, data.service_ids)
        if data.required_specialty_ids is not None:
            await self.care_requests.replace_specialties(cr, data.required_specialty_ids)

        await self.db.commit()
        return await self.care_requests.get_by_id(cr.id)

    async def cancel(self, user_id: uuid.UUID, care_request_id: uuid.UUID) -> CareRequest:
        cr = await self._get_owned(user_id, care_request_id)
        if cr.status not in _CANCELLABLE_STATUSES:
            raise ValidationAppError(
                f"Care request cannot be cancelled while status is {cr.status.value}"
            )
        await self.care_requests.set_status(cr, CareRequestStatus.CANCELLED)
        await self.db.commit()
        return await self.care_requests.get_by_id(cr.id)
