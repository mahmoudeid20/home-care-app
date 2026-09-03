import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus


class ApplicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        care_request_id: uuid.UUID,
        nurse_id: uuid.UUID,
        patient_id: uuid.UUID,
        message: str | None,
    ) -> Application:
        app_ = Application(
            care_request_id=care_request_id,
            nurse_id=nurse_id,
            patient_id=patient_id,
            message=message,
        )
        self.db.add(app_)
        await self.db.flush()
        await self.db.refresh(app_, attribute_names=["created_at", "updated_at"])
        return app_

    async def get_by_id(self, application_id: uuid.UUID) -> Application | None:
        return await self.db.get(Application, application_id)

    async def get_active_for_nurse_and_request(
        self, care_request_id: uuid.UUID, nurse_id: uuid.UUID
    ) -> Application | None:
        result = await self.db.execute(
            select(Application).where(
                Application.care_request_id == care_request_id,
                Application.nurse_id == nurse_id,
                Application.status == ApplicationStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def get_any_for_nurse_and_request(
        self, care_request_id: uuid.UUID, nurse_id: uuid.UUID
    ) -> Application | None:
        """Unlike get_active_for_nurse_and_request (PENDING only, used to
        block duplicate applications), this ignores status — used for read
        access checks: a nurse who has ever applied (accepted, rejected,
        withdrawn, or still pending) should still be able to view the care
        request they applied to."""
        result = await self.db.execute(
            select(Application).where(
                Application.care_request_id == care_request_id,
                Application.nurse_id == nurse_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_other_pending_for_request(
        self, care_request_id: uuid.UUID, exclude_application_id: uuid.UUID
    ) -> list[Application]:
        result = await self.db.execute(
            select(Application).where(
                Application.care_request_id == care_request_id,
                Application.id != exclude_application_id,
                Application.status == ApplicationStatus.PENDING,
            )
        )
        return list(result.scalars().all())

    async def list_received_by_nurse(
        self,
        nurse_id: uuid.UUID,
        status: ApplicationStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Application]:
        stmt = select(Application).where(Application.nurse_id == nurse_id)
        if status is not None:
            stmt = stmt.where(Application.status == status)
        stmt = stmt.order_by(Application.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_sent_by_patient(
        self, patient_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Application]:
        result = await self.db.execute(
            select(Application)
            .where(Application.patient_id == patient_id)
            .order_by(Application.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def set_status(
        self,
        application: Application,
        status: ApplicationStatus,
        rejection_reason: str | None = None,
    ) -> None:
        application.status = status
        if rejection_reason is not None:
            application.rejection_reason = rejection_reason
        await self.db.flush()
