from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_settings import PlatformSettings


class PlatformSettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active(self) -> PlatformSettings:
        result = await self.db.execute(select(PlatformSettings).limit(1))
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = PlatformSettings()
            self.db.add(settings)
            await self.db.flush()
            await self.db.refresh(settings)
            await self.db.commit()
        return settings

    async def update(
        self, settings: PlatformSettings, commission_percentage: float
    ) -> PlatformSettings:
        settings.commission_percentage = commission_percentage
        await self.db.flush()
        await self.db.refresh(settings)
        await self.db.commit()
        return settings
