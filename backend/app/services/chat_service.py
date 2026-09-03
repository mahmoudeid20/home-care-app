"""
Chat business logic shared by the REST endpoints and the WebSocket handler,
so both routes enforce identical authorization and validation rather than
duplicating (and risking drifting) the rules in two places.

Authorization (Section 20): "Users must only access conversations they are
authorized to participate in" - enforced in _require_participant() below,
used by every read/write path.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.conversation import Conversation, Message, MessageType
from app.models.notification import NotificationType
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.nurse_repository import NurseRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.chat import ConversationResponse, MessageCreate
from app.services.notification_service import NotificationService


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversations = ConversationRepository(db)
        self.patients = PatientRepository(db)
        self.nurses = NurseRepository(db)
        self.notifications = NotificationService(db)

    async def get_or_create_conversation(
        self, user_id: uuid.UUID, nurse_id: uuid.UUID
    ) -> Conversation:
        patient = await self.patients.get_by_user_id(user_id)
        if not patient:
            raise NotFoundError("You need a patient profile first")

        nurse = await self.nurses.get_by_id(nurse_id)
        if not nurse:
            raise NotFoundError("Nurse not found")
        if not nurse.is_approved or nurse.is_suspended:
            raise ValidationAppError("This nurse is not currently available for messaging")

        existing = await self.conversations.get_by_patient_and_nurse(patient.id, nurse.id)
        if existing:
            return existing

        conv = await self.conversations.create(patient_id=patient.id, nurse_id=nurse.id)
        await self.db.commit()
        return conv

    async def _require_participant(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> tuple[Conversation, str]:
        conv = await self.conversations.get_by_id(conversation_id)
        if not conv:
            raise NotFoundError("Conversation not found")

        patient = await self.patients.get_by_user_id(user_id)
        if patient and conv.patient_id == patient.id:
            return conv, "patient"

        nurse = await self.nurses.get_by_user_id(user_id)
        if nurse and conv.nurse_id == nurse.id:
            return conv, "nurse"

        raise ForbiddenError("You are not a participant in this conversation")

    async def check_access(self, user_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
        """Used by the WS handler before accepting a connection."""
        conv, _role = await self._require_participant(user_id, conversation_id)
        return conv

    def _preview(self, last: Message | None) -> str | None:
        if not last:
            return None
        if last.message_type == MessageType.TEXT:
            return last.content
        return f"[{last.message_type.value.lower()}]"

    def _to_response(
        self, conv: Conversation, other_party_name: str, last: Message | None
    ) -> ConversationResponse:
        return ConversationResponse(
            id=conv.id,
            patient_id=conv.patient_id,
            nurse_id=conv.nurse_id,
            booking_id=conv.booking_id,
            other_party_name=other_party_name,
            last_message_preview=self._preview(last),
            last_message_at=last.created_at if last else None,
        )

    async def list_my_conversations(self, user_id: uuid.UUID) -> list[ConversationResponse]:
        patient = await self.patients.get_by_user_id(user_id)
        if patient:
            convs = await self.conversations.list_for_patient(patient.id)
            results = []
            for c in convs:
                nurse = await self.nurses.get_by_id(c.nurse_id)
                last = await self.conversations.get_last_message(c.id)
                results.append(self._to_response(c, nurse.full_name, last))
            return results

        nurse = await self.nurses.get_by_user_id(user_id)
        if nurse:
            convs = await self.conversations.list_for_nurse(nurse.id)
            results = []
            for c in convs:
                patient_obj = await self.patients.get_by_id(c.patient_id)
                last = await self.conversations.get_last_message(c.id)
                results.append(self._to_response(c, patient_obj.full_name, last))
            return results

        return []

    async def list_messages(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Message]:
        await self._require_participant(user_id, conversation_id)
        return await self.conversations.list_messages(conversation_id, limit=limit, offset=offset)

    async def send_message(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, data: MessageCreate
    ) -> Message:
        conv, role = await self._require_participant(user_id, conversation_id)
        message = await self.conversations.add_message(
            conversation_id=conv.id,
            sender_id=user_id,
            message_type=data.message_type,
            content=data.content,
            attachment_url=data.attachment_url,
        )
        await self.conversations.touch(conv)

        patient = await self.patients.get_by_id(conv.patient_id)
        nurse = await self.nurses.get_by_id(conv.nurse_id)
        recipient_user_id = nurse.user_id if role == "patient" else patient.user_id
        sender_name = patient.full_name if role == "patient" else nurse.full_name
        preview = data.content if data.message_type == MessageType.TEXT else f"Sent a {data.message_type.value.lower()}"
        await self.notifications.notify(
            user_id=recipient_user_id,
            type_=NotificationType.NEW_MESSAGE,
            title=f"New message from {sender_name}",
            body=preview or "",
            data={"conversation_id": str(conv.id), "message_id": str(message.id)},
        )

        await self.db.commit()
        return message
