import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus


class BookingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **fields) -> Booking:
        booking = Booking(**fields)
        self.db.add(booking)
        await self.db.flush()
        await self.db.refresh(booking, attribute_names=["created_at", "updated_at"])
        return booking

    async def get_by_id(self, booking_id: uuid.UUID) -> Booking | None:
        return await self.db.get(Booking, booking_id)

    async def get_by_application_id(self, application_id: uuid.UUID) -> Booking | None:
        result = await self.db.execute(
            select(Booking).where(Booking.application_id == application_id)
        )
        return result.scalar_one_or_none()

    async def list_for_patient(
        self, patient_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Booking]:
        result = await self.db.execute(
            select(Booking)
            .where(Booking.patient_id == patient_id)
            .order_by(Booking.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_for_nurse(
        self, nurse_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Booking]:
        result = await self.db.execute(
            select(Booking)
            .where(Booking.nurse_id == nurse_id)
            .order_by(Booking.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def set_status(self, booking: Booking, status: BookingStatus) -> None:
        booking.status = status
        await self.db.flush()
