"""Complaint filing and admin triage (Section 29)."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.complaint import Complaint, ComplaintStatus
from app.repositories.admin_action_repository import AdminActionRepository
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.complaint import ComplaintAdminUpdate, ComplaintCreate


class ComplaintService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.complaints = ComplaintRepository(db)
        self.audit = AdminActionRepository(db)

    async def create(self, user_id: uuid.UUID, data: ComplaintCreate) -> Complaint:
        complaint = await self.complaints.create(
            user_id=user_id,
            booking_id=data.booking_id,
            category=data.category,
            description=data.description,
            attachments=data.attachments,
        )
        await self.db.commit()
        return complaint

    async def list_mine(self, user_id: uuid.UUID, limit: int = 20, offset: int = 0) -> list[Complaint]:
        return await self.complaints.list_for_user(user_id, limit=limit, offset=offset)

    async def get_own(self, user_id: uuid.UUID, complaint_id: uuid.UUID) -> Complaint:
        complaint = await self.complaints.get_by_id(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint not found")
        if complaint.user_id != user_id:
            raise ForbiddenError("Not your complaint")
        return complaint

    async def list_all(
        self, status: ComplaintStatus | None = None, limit: int = 20, offset: int = 0
    ) -> list[Complaint]:
        return await self.complaints.list_all(status=status, limit=limit, offset=offset)

    async def admin_update(
        self, admin_id: uuid.UUID, complaint_id: uuid.UUID, data: ComplaintAdminUpdate
    ) -> Complaint:
        complaint = await self.complaints.get_by_id(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint not found")
        await self.complaints.update(complaint, status=data.status, admin_response=data.admin_response)
        await self.audit.record(
            admin_id=admin_id,
            action_type="UPDATE_COMPLAINT",
            target_type="complaint",
            target_id=complaint.id,
            reason=data.admin_response,
        )
        await self.db.commit()
        return complaint
