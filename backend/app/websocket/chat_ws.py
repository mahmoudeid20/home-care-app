"""
WebSocket chat endpoint (Section 20).

Browsers can't set an Authorization header on a WebSocket handshake, so the
access token is passed as a query parameter (?token=...) - the same access
token issued by /auth/login, just carried differently for this one route.
Every inbound frame still goes through the same ChatService authorization
check used by the REST endpoints (Section 20: "Users must only access
conversations they are authorized to participate in").

Note: this uses `db: AsyncSession = Depends(get_db)` like every other
endpoint in the app (FastAPI supports Depends() on WebSocket routes too),
rather than opening a session directly via AsyncSessionLocal. That keeps
it consistent with the rest of the codebase and, importantly, means it
respects dependency_overrides in tests instead of silently connecting to
the real configured database.

Client protocol (JSON frames):
  Send:    {"message_type": "TEXT", "content": "..."}
           {"message_type": "IMAGE", "attachment_url": "...", "content": "optional caption"}
  Receive: the persisted message, broadcast to the other participant(s)
           currently connected to this conversation.
"""
import uuid

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.chat import MessageCreate, MessageResponse
from app.services.chat_service import ChatService
from app.websocket.connection_manager import chat_connection_manager

router = APIRouter()


@router.websocket("/ws/conversations/{conversation_id}")
async def chat_websocket(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = decode_token(token, token_type="access")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        await websocket.close(code=4401)
        return

    service = ChatService(db)
    try:
        await service.check_access(user_id, conversation_id)
    except Exception:
        await websocket.close(code=4403)
        return

    await chat_connection_manager.connect(conversation_id, websocket)
    try:
        while True:
            raw = await websocket.receive_json()
            try:
                data = MessageCreate(**raw)
                message = await service.send_message(user_id, conversation_id, data)
            except (ValidationError, Exception) as exc:
                await websocket.send_json({"error": str(exc)})
                continue

            payload_out = MessageResponse.model_validate(message).model_dump(mode="json")
            await chat_connection_manager.broadcast(conversation_id, payload_out)
    except WebSocketDisconnect:
        pass
    finally:
        chat_connection_manager.disconnect(conversation_id, websocket)
