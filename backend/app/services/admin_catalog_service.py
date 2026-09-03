"""
Services/specialties catalog management (Section 9: "The service list must
be configurable from the admin dashboard" / Section 26). Every create or
update is audit-logged.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.admin_action_repository import AdminActionRepository
from app.repositories.lookup_repository import LookupRepository
from app.schemas.admin import ServiceUpsertRequest, SpecialtyUpsertRequest


class AdminCatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.lookup = LookupRepository(db)
        self.audit = AdminActionRepository(db)

    async def create_service(self, admin_id: uuid.UUID, data: ServiceUpsertRequest):
        service = await self.lookup.create_service(data.name_en, data.name_ar, data.is_active)
        await self.audit.record(admin_id, "CREATE_SERVICE", "service", service.id)
        await self.db.commit()
        return service

    async def update_service(self, admin_id: uuid.UUID, service_id: uuid.UUID, data: ServiceUpsertRequest):
        service = await self.lookup.get_service_by_id(service_id)
        if not service:
            raise NotFoundError("Service not found")
        service = await self.lookup.update_service(service, data.name_en, data.name_ar, data.is_active)
        await self.audit.record(admin_id, "UPDATE_SERVICE", "service", service.id)
        await self.db.commit()
        return service

    async def create_specialty(self, admin_id: uuid.UUID, data: SpecialtyUpsertRequest):
        specialty = await self.lookup.create_specialty(data.name_en, data.name_ar, data.is_active)
        await self.audit.record(admin_id, "CREATE_SPECIALTY", "specialty", specialty.id)
        await self.db.commit()
        return specialty

    async def update_specialty(
        self, admin_id: uuid.UUID, specialty_id: uuid.UUID, data: SpecialtyUpsertRequest
    ):
        specialty = await self.lookup.get_specialty_by_id(specialty_id)
        if not specialty:
            raise NotFoundError("Specialty not found")
        specialty = await self.lookup.update_specialty(
            specialty, data.name_en, data.name_ar, data.is_active
        )
        await self.audit.record(admin_id, "UPDATE_SPECIALTY", "specialty", specialty.id)
        await self.db.commit()
        return specialty
