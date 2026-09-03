import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message, MessageType


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_patient_and_nurse(
        self, patient_id: uuid.UUID, nurse_id: uuid.UUID
    ) -> Conversation | None:
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.patient_id == patient_id, Conversation.nurse_id == nurse_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        return await self.db.get(Conversation, conversation_id)

    async def create(
        self, patient_id: uuid.UUID, nurse_id: uuid.UUID, booking_id: uuid.UUID | None = None
    ) -> Conversation:
        conv = Conversation(patient_id=patient_id, nurse_id=nurse_id, booking_id=booking_id)
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv, attribute_names=["created_at", "updated_at"])
        return conv

    async def list_for_patient(self, patient_id: uuid.UUID) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.patient_id == patient_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_for_nurse(self, nurse_id: uuid.UUID) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.nurse_id == nurse_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def touch(self, conversation: Conversation) -> None:
        """Bump updated_at so the conversation list can sort by recency."""
        conversation.updated_at = func.now()
        await self.db.flush()

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        message_type: MessageType,
        content: str | None,
        attachment_url: str | None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            message_type=message_type,
            content=content,
            attachment_url=attachment_url,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message, attribute_names=["created_at"])
        return message

    async def list_messages(
        self, conversation_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(reversed(result.scalars().all()))

    async def get_last_message(self, conversation_id: uuid.UUID) -> Message | None:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
