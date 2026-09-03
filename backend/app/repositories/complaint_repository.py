import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint, ComplaintStatus


class ComplaintRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **fields) -> Complaint:
        complaint = Complaint(**fields)
        self.db.add(complaint)
        await self.db.flush()
        await self.db.refresh(complaint, attribute_names=["created_at", "updated_at"])
        return complaint

    async def get_by_id(self, complaint_id: uuid.UUID) -> Complaint | None:
        return await self.db.get(Complaint, complaint_id)

    async def list_for_user(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Complaint]:
        result = await self.db.execute(
            select(Complaint)
            .where(Complaint.user_id == user_id)
            .order_by(Complaint.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_all(
        self, status: ComplaintStatus | None = None, limit: int = 20, offset: int = 0
    ) -> list[Complaint]:
        stmt = select(Complaint)
        if status is not None:
            stmt = stmt.where(Complaint.status == status)
        stmt = stmt.order_by(Complaint.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, complaint: Complaint, status: ComplaintStatus, admin_response: str | None = None
    ) -> None:
        complaint.status = status
        if admin_response is not None:
            complaint.admin_response = admin_response
        await self.db.flush()
