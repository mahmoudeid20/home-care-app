import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.schemas.lookup import LocationInput


class LocationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: LocationInput) -> Location:
        location = Location(**data.model_dump())
        self.db.add(location)
        await self.db.flush()
        await self.db.refresh(location)
        return location

    async def update(self, location: Location, data: LocationInput) -> Location:
        for field, value in data.model_dump().items():
            setattr(location, field, value)
        await self.db.flush()
        await self.db.refresh(location)
        return location

    async def get_by_id(self, location_id: uuid.UUID) -> Location | None:
        return await self.db.get(Location, location_id)
