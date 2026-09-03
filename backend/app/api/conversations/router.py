import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["Chat"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start (or resume) a conversation with a nurse",
    description=(
        "PATIENT role only, mirrors the 'Message' button on a nurse's "
        "public profile (Section 16). Idempotent: if a conversation with "
        "this nurse already exists, it is returned instead of creating a "
        "duplicate."
    ),
    responses={
        404: {"description": "Nurse not found, or no patient profile yet"},
        422: {"description": "Nurse not currently available for messaging"},
    },
)
async def start_conversation(
    payload: ConversationCreate,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: ChatService = Depends(get_chat_service),
) -> ConversationResponse:
    conv = await service.get_or_create_conversation(user.id, payload.nurse_id)
    conversations = await service.list_my_conversations(user.id)
    return next(c for c in conversations if c.id == conv.id)


@router.get(
    "",
    response_model=list[ConversationResponse],
    summary="List the current user's conversations (patient or nurse)",
)
async def list_conversations(
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: ChatService = Depends(get_chat_service),
) -> list[ConversationResponse]:
    return await service.list_my_conversations(user.id)


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
    summary="List messages in a conversation (participants only)",
    responses={
        403: {"description": "Not a participant in this conversation"},
        404: {"description": "Conversation not found"},
    },
)
async def list_messages(
    conversation_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: ChatService = Depends(get_chat_service),
) -> list[MessageResponse]:
    messages = await service.list_messages(user.id, conversation_id, limit=limit, offset=offset)
    return [MessageResponse.model_validate(m) for m in messages]


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message (REST fallback; the WebSocket endpoint delivers in real time)",
    description=(
        "Persists a text, image, or file message. Use this for sending "
        "attachments after uploading them to storage, or as a fallback "
        "when a WebSocket connection is not available. For real-time "
        "delivery, connect to /ws/conversations/{conversation_id}?token=..."
    ),
    responses={
        403: {"description": "Not a participant in this conversation"},
        404: {"description": "Conversation not found"},
        422: {"description": "Missing content/attachment_url for the given message_type"},
    },
)
async def send_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: ChatService = Depends(get_chat_service),
) -> MessageResponse:
    message = await service.send_message(user.id, conversation_id, payload)
    return MessageResponse.model_validate(message)
