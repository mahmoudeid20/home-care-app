import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_action import AdminAction


class AdminActionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record(
        self,
        admin_id: uuid.UUID,
        action_type: str,
        target_type: str,
        target_id: uuid.UUID,
        reason: str | None = None,
    ) -> AdminAction:
        action = AdminAction(
            admin_id=admin_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
        )
        self.db.add(action)
        await self.db.flush()
        return action

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[AdminAction]:
        result = await self.db.execute(
            select(AdminAction).order_by(AdminAction.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
