import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: uuid.UUID) -> Patient | None:
        result = await self.db.execute(
            select(Patient).options(selectinload(Patient.location)).where(Patient.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, patient_id: uuid.UUID) -> Patient | None:
        result = await self.db.execute(
            select(Patient).options(selectinload(Patient.location)).where(Patient.id == patient_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        full_name: str,
        preferred_language: str,
        location_id: uuid.UUID | None,
        photo_url: str | None = None,
    ) -> Patient:
        patient = Patient(
            user_id=user_id,
            full_name=full_name,
            preferred_language=preferred_language,
            photo_url=photo_url,
            location_id=location_id,
        )
        self.db.add(patient)
        await self.db.flush()
        # Scoped refresh only — see NurseRepository.create for why a full
        # refresh() (which would expire the `location` relationship too) is
        # avoided here.
        await self.db.refresh(patient, attribute_names=["created_at", "updated_at"])
        return patient
