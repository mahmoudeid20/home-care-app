import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nurse import Gender, Nurse, PriceUnit, ShiftType
from app.repositories.nurse_repository import NurseRepository


class NurseSearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.nurses = NurseRepository(db)

    async def search(
        self,
        gender: Gender | None = None,
        min_experience_years: int | None = None,
        specialty_id: uuid.UUID | None = None,
        min_rating: float | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        payment_frequency: PriceUnit | None = None,
        shift_type: ShiftType | None = None,
        verified_only: bool = False,
        governorate: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Nurse]:
        return await self.nurses.search(
            gender=gender,
            min_experience_years=min_experience_years,
            specialty_id=specialty_id,
            min_rating=min_rating,
            price_min=price_min,
            price_max=price_max,
            payment_frequency=payment_frequency,
            shift_type=shift_type,
            verified_only=verified_only,
            governorate=governorate,
            limit=limit,
            offset=offset,
        )
