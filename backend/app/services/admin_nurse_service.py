"""
Nurse verification workflow (Section 17, 28). Approving a document flips
the corresponding coarse verification flag on the Nurse (identity/
qualification/experience); a separate explicit "approve nurse" action is
still required to flip `is_approved` (Section 28 lists "Approve nurse" as
its own admin action, distinct from document review) and requires all
three flags to already be true. Every mutating action is written to the
audit log (Section 28) and triggers a notification to the nurse
(Section 25: "Document verification result").
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.nurse import DocumentStatus, DocumentType, Nurse, NurseDocument
from app.models.notification import NotificationType
from app.repositories.admin_action_repository import AdminActionRepository
from app.repositories.nurse_repository import NurseRepository
from app.services.notification_service import NotificationService

_QUALIFICATION_DOC_TYPES = {DocumentType.NURSING_CERTIFICATE, DocumentType.GRADUATION_CERTIFICATE}
_EXPERIENCE_DOC_TYPES = {DocumentType.EXPERIENCE_CERTIFICATE}


class AdminNurseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.nurses = NurseRepository(db)
        self.audit = AdminActionRepository(db)
        self.notifications = NotificationService(db)

    async def list_nurses(
        self,
        is_approved: bool | None = None,
        pending_verification: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Nurse]:
        return await self.nurses.list_all_admin(
            is_approved=is_approved,
            pending_verification=pending_verification,
            limit=limit,
            offset=offset,
        )

    async def get_documents(self, nurse_id: uuid.UUID) -> list[NurseDocument]:
        nurse = await self.nurses.get_by_id(nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        return await self.nurses.list_documents(nurse_id)

    async def _flag_field_for_document_type(self, doc_type: DocumentType) -> str | None:
        if doc_type == DocumentType.NATIONAL_ID:
            return "identity_verified"
        if doc_type in _QUALIFICATION_DOC_TYPES:
            return "qualification_verified"
        if doc_type in _EXPERIENCE_DOC_TYPES:
            return "experience_verified"
        return None

    async def approve_document(
        self, admin_id: uuid.UUID, nurse_id: uuid.UUID, document_id: uuid.UUID
    ) -> NurseDocument:
        nurse = await self.nurses.get_by_id(nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        document = await self.nurses.get_document_by_id(document_id)
        if not document or document.nurse_id != nurse_id:
            raise NotFoundError("Document not found")

        await self.nurses.set_document_status(document, DocumentStatus.APPROVED, reviewed_by=admin_id)

        flag_field = await self._flag_field_for_document_type(document.document_type)
        if flag_field:
            setattr(nurse, flag_field, True)
            await self.db.flush()

        await self.audit.record(
            admin_id=admin_id,
            action_type="APPROVE_DOCUMENT",
            target_type="nurse_document",
            target_id=document.id,
        )
        await self.notifications.notify(
            user_id=nurse.user_id,
            type_=NotificationType.DOCUMENT_VERIFICATION_RESULT,
            title="Document approved",
            body=f"Your {document.document_type.value.replace('_', ' ').title()} was approved.",
            data={"document_id": str(document.id), "status": "APPROVED"},
        )
        await self.db.commit()
        return document

    async def reject_document(
        self, admin_id: uuid.UUID, nurse_id: uuid.UUID, document_id: uuid.UUID, reason: str | None
    ) -> NurseDocument:
        nurse = await self.nurses.get_by_id(nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        document = await self.nurses.get_document_by_id(document_id)
        if not document or document.nurse_id != nurse_id:
            raise NotFoundError("Document not found")

        await self.nurses.set_document_status(
            document, DocumentStatus.REJECTED, reviewed_by=admin_id, rejection_reason=reason
        )

        await self.audit.record(
            admin_id=admin_id,
            action_type="REJECT_DOCUMENT",
            target_type="nurse_document",
            target_id=document.id,
            reason=reason,
        )
        await self.notifications.notify(
            user_id=nurse.user_id,
            type_=NotificationType.DOCUMENT_VERIFICATION_RESULT,
            title="Document rejected",
            body=reason or f"Your {document.document_type.value.replace('_', ' ').title()} was rejected.",
            data={"document_id": str(document.id), "status": "REJECTED"},
        )
        await self.db.commit()
        return document

    async def approve_nurse(self, admin_id: uuid.UUID, nurse_id: uuid.UUID) -> Nurse:
        nurse = await self.nurses.get_by_id(nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        if not nurse.is_fully_verified:
            raise ValidationAppError(
                "Nurse cannot be approved until identity, qualification, and experience "
                "documents are all verified"
            )
        await self.nurses.set_approval(nurse, True)
        await self.audit.record(
            admin_id=admin_id, action_type="APPROVE_NURSE", target_type="nurse", target_id=nurse.id
        )
        await self.db.commit()
        return nurse

    async def suspend_nurse(
        self, admin_id: uuid.UUID, nurse_id: uuid.UUID, reason: str | None
    ) -> Nurse:
        nurse = await self.nurses.get_by_id(nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        await self.nurses.set_suspended(nurse, True)
        await self.audit.record(
            admin_id=admin_id,
            action_type="SUSPEND_NURSE",
            target_type="nurse",
            target_id=nurse.id,
            reason=reason,
        )
        await self.db.commit()
        return nurse

    async def reactivate_nurse(self, admin_id: uuid.UUID, nurse_id: uuid.UUID) -> Nurse:
        nurse = await self.nurses.get_by_id(nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        await self.nurses.set_suspended(nurse, False)
        await self.audit.record(
            admin_id=admin_id,
            action_type="REACTIVATE_NURSE",
            target_type="nurse",
            target_id=nurse.id,
        )
        await self.db.commit()
        return nurse
