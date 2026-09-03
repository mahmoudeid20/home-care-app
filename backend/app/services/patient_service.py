import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.patient import Patient
from app.repositories.location_repository import LocationRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.lookup import LocationInput
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest


class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.patients = PatientRepository(db)
        self.locations = LocationRepository(db)

    async def create_profile(self, user_id: uuid.UUID, data: PatientCreateRequest) -> Patient:
        if await self.patients.get_by_user_id(user_id):
            raise ConflictError("A patient profile already exists for this account")

        location_id = None
        if data.location:
            location = await self.locations.create(data.location)
            location_id = location.id

        patient = await self.patients.create(
            user_id=user_id,
            full_name=data.full_name,
            national_id=data.national_id,
            preferred_language=data.preferred_language,
            photo_url=data.photo_url,
            location_id=location_id,
        )
        await self.db.commit()
        return await self.patients.get_by_user_id(user_id)  # reload with relationships

    async def get_my_profile(self, user_id: uuid.UUID) -> Patient:
        patient = await self.patients.get_by_user_id(user_id)
        if not patient:
            raise NotFoundError("Patient profile not found. Create one first.")
        return patient

    async def update_profile(self, user_id: uuid.UUID, data: PatientUpdateRequest) -> Patient:
        patient = await self.get_my_profile(user_id)

        if data.full_name is not None:
            patient.full_name = data.full_name
        if data.national_id is not None:
            patient.national_id = data.national_id
        if data.preferred_language is not None:
            patient.preferred_language = data.preferred_language
        if data.photo_url is not None:
            patient.photo_url = data.photo_url
        if data.location is not None:
            if patient.location_id:
                existing = await self.locations.get_by_id(patient.location_id)
                await self.locations.update(existing, data.location)
                # Keep the in-memory relationship in sync: the session's
                # identity map may otherwise return this same Patient object
                # on the next query with a stale `location` attribute since
                # expire_on_commit=False (updating location_id alone would
                # not automatically refresh the loaded relationship).
                patient.location = existing
            else:
                new_location = await self.locations.create(data.location)
                patient.location_id = new_location.id
                patient.location = new_location

        await self.db.commit()
        return await self.patients.get_by_user_id(user_id)
