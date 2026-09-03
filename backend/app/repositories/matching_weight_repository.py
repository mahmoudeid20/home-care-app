from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.matching_weight import MatchingWeights


class MatchingWeightsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active(self) -> MatchingWeights:
        """
        Returns the single active weights row, creating it with Section 21's
        default percentages on first use so the matching engine works
        out-of-the-box without requiring a manual admin setup step.
        """
        result = await self.db.execute(select(MatchingWeights).limit(1))
        weights = result.scalar_one_or_none()
        if weights is None:
            weights = MatchingWeights()
            self.db.add(weights)
            await self.db.flush()
            await self.db.refresh(weights)
            await self.db.commit()
        return weights

    async def update(self, weights: MatchingWeights, **fields) -> MatchingWeights:
        for key, value in fields.items():
            setattr(weights, key, value)
        await self.db.flush()
        await self.db.refresh(weights)
        await self.db.commit()
        return weights
