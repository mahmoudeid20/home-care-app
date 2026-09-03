import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.care_request import (
    CareRequest,
    CareRequestRequirement,
    CareRequestService,
    CareRequestSpecialty,
    CareRequestStatus,
)


def _load_options():
    return (
        selectinload(CareRequest.location),
        selectinload(CareRequest.required_services).selectinload(CareRequestService.service),
        selectinload(CareRequest.required_specialties).selectinload(CareRequestSpecialty.specialty),
    )


class CareRequestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **fields) -> CareRequest:
        cr = CareRequest(**fields)
        self.db.add(cr)
        await self.db.flush()
        # Scoped refresh only — see NurseRepository.create for rationale
        # (avoid expiring not-yet-touched relationship attributes, which
        # would trigger an implicit sync lazy-load in async SQLAlchemy).
        await self.db.refresh(cr, attribute_names=["created_at", "updated_at"])
        return cr

    async def get_by_id(self, care_request_id: uuid.UUID) -> CareRequest | None:
        result = await self.db.execute(
            select(CareRequest).options(*_load_options()).where(CareRequest.id == care_request_id)
        )
        return result.scalar_one_or_none()

    async def list_by_patient(
        self, patient_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[CareRequest]:
        result = await self.db.execute(
            select(CareRequest)
            .options(*_load_options())
            .where(CareRequest.patient_id == patient_id)
            .order_by(CareRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def replace_services(self, care_request: CareRequest, service_ids: list[uuid.UUID]) -> None:
        await self.db.execute(
            delete(CareRequestService).where(CareRequestService.care_request_id == care_request.id)
        )
        await self.db.flush()
        for service_id in service_ids:
            self.db.add(
                CareRequestService(care_request_id=care_request.id, service_id=service_id)
            )
        await self.db.flush()

    async def replace_specialties(
        self, care_request: CareRequest, specialty_ids: list[uuid.UUID]
    ) -> None:
        await self.db.execute(
            delete(CareRequestSpecialty).where(
                CareRequestSpecialty.care_request_id == care_request.id
            )
        )
        await self.db.flush()
        for specialty_id in specialty_ids:
            self.db.add(
                CareRequestSpecialty(care_request_id=care_request.id, specialty_id=specialty_id)
            )
        await self.db.flush()

    async def set_status(self, care_request: CareRequest, status: CareRequestStatus) -> None:
        care_request.status = status
        await self.db.flush()
