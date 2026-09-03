from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
from app.models.specialty import Specialty


class LookupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_specialties(self, active_only: bool = True) -> list[Specialty]:
        stmt = select(Specialty)
        if active_only:
            stmt = stmt.where(Specialty.is_active.is_(True))
        result = await self.db.execute(stmt.order_by(Specialty.name_en))
        return list(result.scalars().all())

    async def list_services(self, active_only: bool = True) -> list[Service]:
        stmt = select(Service)
        if active_only:
            stmt = stmt.where(Service.is_active.is_(True))
        result = await self.db.execute(stmt.order_by(Service.name_en))
        return list(result.scalars().all())

    async def create_service(self, name_en: str, name_ar: str, is_active: bool) -> Service:
        service = Service(name_en=name_en, name_ar=name_ar, is_active=is_active)
        self.db.add(service)
        await self.db.flush()
        await self.db.refresh(service)
        return service

    async def get_service_by_id(self, service_id) -> Service | None:
        return await self.db.get(Service, service_id)

    async def update_service(self, service: Service, name_en: str, name_ar: str, is_active: bool) -> Service:
        service.name_en = name_en
        service.name_ar = name_ar
        service.is_active = is_active
        await self.db.flush()
        await self.db.refresh(service)
        return service

    async def create_specialty(self, name_en: str, name_ar: str, is_active: bool) -> Specialty:
        specialty = Specialty(name_en=name_en, name_ar=name_ar, is_active=is_active)
        self.db.add(specialty)
        await self.db.flush()
        await self.db.refresh(specialty)
        return specialty

    async def get_specialty_by_id(self, specialty_id) -> Specialty | None:
        return await self.db.get(Specialty, specialty_id)

    async def update_specialty(
        self, specialty: Specialty, name_en: str, name_ar: str, is_active: bool
    ) -> Specialty:
        specialty.name_en = name_en
        specialty.name_ar = name_ar
        specialty.is_active = is_active
        await self.db.flush()
        await self.db.refresh(specialty)
        return specialty
