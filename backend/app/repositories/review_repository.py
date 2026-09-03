import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_booking_id(self, booking_id: uuid.UUID) -> Review | None:
        result = await self.db.execute(select(Review).where(Review.booking_id == booking_id))
        return result.scalar_one_or_none()

    async def create(self, **fields) -> Review:
        review = Review(**fields)
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review, attribute_names=["created_at", "updated_at"])
        return review

    async def list_for_nurse(
        self, nurse_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Review]:
        result = await self.db.execute(
            select(Review)
            .where(Review.nurse_id == nurse_id)
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
