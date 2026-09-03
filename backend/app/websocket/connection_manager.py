"""
In-memory broadcast registry for chat WebSocket connections, keyed by
conversation id. Sufficient for a single-instance MVP deployment.

Scaling note (Section 20: Redis if required for realtime infrastructure):
once the API runs across multiple instances, a connection on instance A
can't directly push to a socket held open on instance B. At that point,
swap the in-process connections dict for a Redis pub/sub channel per
conversation (publish on send, each instance subscribes and forwards to
its own locally-held sockets) - the public interface below (connect,
disconnect, broadcast) would stay the same, so callers would not change.
"""
import uuid

from fastapi import WebSocket


class ChatConnectionManager:
    def __init__(self):
        self._connections: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(conversation_id, set()).add(websocket)

    def disconnect(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        sockets = self._connections.get(conversation_id)
        if sockets:
            sockets.discard(websocket)
            if not sockets:
                self._connections.pop(conversation_id, None)

    async def broadcast(
        self, conversation_id: uuid.UUID, payload: dict, exclude: WebSocket | None = None
    ) -> None:
        sockets = self._connections.get(conversation_id, set())
        dead = []
        for ws in sockets:
            if ws is exclude:
                continue
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            sockets.discard(ws)


chat_connection_manager = ChatConnectionManager()
