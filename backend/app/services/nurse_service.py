import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.nurse import Nurse
from app.repositories.location_repository import LocationRepository
from app.repositories.lookup_repository import LookupRepository
from app.repositories.nurse_repository import NurseRepository
from app.schemas.nurse import (
    NurseCreateRequest,
    NurseDocumentUploadRequest,
    NurseUpdateRequest,
)


class NurseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.nurses = NurseRepository(db)
        self.locations = LocationRepository(db)
        self.lookup = LookupRepository(db)

    async def _validate_specialty_ids(self, specialty_ids: list[uuid.UUID]) -> None:
        if not specialty_ids:
            return
        valid = {s.id for s in await self.lookup.list_specialties(active_only=False)}
        unknown = set(specialty_ids) - valid
        if unknown:
            raise ValidationAppError(f"Unknown specialty id(s): {sorted(str(u) for u in unknown)}")

    async def _validate_service_ids(self, service_ids: list[uuid.UUID]) -> None:
        if not service_ids:
            return
        valid = {s.id for s in await self.lookup.list_services(active_only=False)}
        unknown = set(service_ids) - valid
        if unknown:
            raise ValidationAppError(f"Unknown service id(s): {sorted(str(u) for u in unknown)}")

    async def create_profile(self, user_id: uuid.UUID, data: NurseCreateRequest) -> Nurse:
        if await self.nurses.get_by_user_id(user_id):
            raise ConflictError("A nurse profile already exists for this account")

        await self._validate_specialty_ids(data.specialty_ids)
        await self._validate_service_ids([s.service_id for s in data.services])

        location_id = None
        if data.location:
            location = await self.locations.create(data.location)
            location_id = location.id

        nurse = await self.nurses.create(
            user_id=user_id,
            full_name=data.full_name,
            professional_title=data.professional_title,
            bio=data.bio,
            gender=data.gender,
            date_of_birth=data.date_of_birth,
            experience_years=data.experience_years,
            education=data.education,
            photo_url=data.photo_url,
            location_id=location_id,
        )

        if data.specialty_ids:
            await self.nurses.replace_specialties(nurse, data.specialty_ids)
        if data.services:
            await self.nurses.replace_services(
                nurse, [s.model_dump() for s in data.services]
            )
        if data.availability:
            await self.nurses.replace_availability(
                nurse, [a.model_dump() for a in data.availability]
            )

        await self.db.commit()
        return await self.nurses.get_by_user_id(user_id)

    async def get_my_profile(self, user_id: uuid.UUID) -> Nurse:
        nurse = await self.nurses.get_by_user_id(user_id)
        if not nurse:
            raise NotFoundError("Nurse profile not found. Create one first.")
        return nurse

    async def get_public_profile(self, nurse_id: uuid.UUID) -> Nurse:
        nurse = await self.nurses.get_by_id(nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        return nurse

    async def update_profile(self, user_id: uuid.UUID, data: NurseUpdateRequest) -> Nurse:
        nurse = await self.get_my_profile(user_id)

        if data.full_name is not None:
            nurse.full_name = data.full_name
        if data.professional_title is not None:
            nurse.professional_title = data.professional_title
        if data.bio is not None:
            nurse.bio = data.bio
        if data.experience_years is not None:
            nurse.experience_years = data.experience_years
        if data.education is not None:
            nurse.education = data.education
        if data.photo_url is not None:
            nurse.photo_url = data.photo_url

        if data.location is not None:
            if nurse.location_id:
                existing = await self.locations.get_by_id(nurse.location_id)
                await self.locations.update(existing, data.location)
                # See PatientService.update_profile for why this explicit
                # relationship assignment is needed (identity-map staleness).
                nurse.location = existing
            else:
                new_location = await self.locations.create(data.location)
                nurse.location_id = new_location.id
                nurse.location = new_location

        if data.specialty_ids is not None:
            await self._validate_specialty_ids(data.specialty_ids)
            await self.nurses.replace_specialties(nurse, data.specialty_ids)

        if data.services is not None:
            await self._validate_service_ids([s.service_id for s in data.services])
            await self.nurses.replace_services(nurse, [s.model_dump() for s in data.services])

        if data.availability is not None:
            await self.nurses.replace_availability(
                nurse, [a.model_dump() for a in data.availability]
            )

        await self.db.commit()
        return await self.nurses.get_by_user_id(user_id)

    async def upload_document(self, user_id: uuid.UUID, data: NurseDocumentUploadRequest):
        nurse = await self.get_my_profile(user_id)
        doc = await self.nurses.add_document(
            nurse_id=nurse.id, document_type=data.document_type, file_url=data.file_url
        )
        await self.db.commit()
        return doc

    async def list_my_documents(self, user_id: uuid.UUID):
        nurse = await self.get_my_profile(user_id)
        return await self.nurses.list_documents(nurse.id)
