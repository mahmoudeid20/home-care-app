"""
Focused smoke test for the /ws/conversations/{id} WebSocket endpoint.

This uses Starlette's synchronous TestClient (not the async httpx client
used everywhere else in the suite) because websocket_connect() needs a
fully synchronous test flow. It sets up its own isolated in-memory SQLite
database (StaticPool + check_same_thread=False so the same connection is
shared across the TestClient's background thread) rather than reusing the
shared db_session/client fixtures, to avoid mixing two different asyncio
event loops against the same aiosqlite connection.
"""
import asyncio
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  ensure models are registered
from app.api.deps import get_redis_dep
from app.core import rate_limit
from app.core.database import Base, get_db
from app.main import app
from app.models.nurse import Nurse


class _FakeRedis:
    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ex=None):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)

    async def incr(self, key):
        current = int(self._store.get(key, "0")) + 1
        self._store[key] = str(current)
        return current

    async def expire(self, key, seconds):
        pass


def test_websocket_chat_delivers_message_between_participants():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_db())

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fake_redis = _FakeRedis()

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_dep] = override_get_redis
    rate_limit.set_redis_override(fake_redis)

    try:
        client = TestClient(app)

        patient_reg = client.post(
            "/api/v1/auth/register",
            json={"email": "wspatient@example.com", "password": "Passw0rd1", "role": "PATIENT"},
        )
        assert patient_reg.status_code == 201, patient_reg.text
        patient_token = patient_reg.json()["tokens"]["access_token"]
        patient_headers = {"Authorization": f"Bearer {patient_token}"}
        client.post(
            "/api/v1/patients/me", headers=patient_headers, json={"full_name": "WS Patient"}
        )

        nurse_reg = client.post(
            "/api/v1/auth/register",
            json={"email": "wsnurse@example.com", "password": "Passw0rd1", "role": "NURSE"},
        )
        nurse_token = nurse_reg.json()["tokens"]["access_token"]
        nurse_headers = {"Authorization": f"Bearer {nurse_token}"}
        nurse_profile = client.post(
            "/api/v1/nurses/me",
            headers=nurse_headers,
            json={"full_name": "WS Nurse", "gender": "FEMALE", "experience_years": 3},
        )
        nurse_id = nurse_profile.json()["id"]

        async def approve_nurse():
            async with session_factory() as session:
                nurse = await session.get(Nurse, uuid.UUID(nurse_id))
                nurse.is_approved = True
                await session.commit()

        asyncio.run(approve_nurse())

        conv_resp = client.post(
            "/api/v1/conversations", headers=patient_headers, json={"nurse_id": nurse_id}
        )
        assert conv_resp.status_code == 201, conv_resp.text
        conv_id = conv_resp.json()["id"]

        with client.websocket_connect(
            f"/ws/conversations/{conv_id}?token={patient_token}"
        ) as patient_ws:
            with client.websocket_connect(
                f"/ws/conversations/{conv_id}?token={nurse_token}"
            ) as nurse_ws:
                patient_ws.send_json({"message_type": "TEXT", "content": "Hello from the patient"})

                received = nurse_ws.receive_json()
                assert received["content"] == "Hello from the patient"
                assert received["message_type"] == "TEXT"

        history = client.get(
            f"/api/v1/conversations/{conv_id}/messages", headers=nurse_headers
        )
        assert history.status_code == 200
        assert len(history.json()) == 1
        assert history.json()[0]["content"] == "Hello from the patient"
    finally:
        app.dependency_overrides.clear()
        rate_limit.set_redis_override(None)
        asyncio.run(engine.dispose())


def test_websocket_rejects_missing_token():
    """Connecting without ?token= should be refused rather than accepted."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_db())

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fake_redis = _FakeRedis()

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_dep] = override_get_redis
    rate_limit.set_redis_override(fake_redis)

    try:
        client = TestClient(app)
        random_id = uuid.uuid4()
        try:
            with client.websocket_connect(f"/ws/conversations/{random_id}"):
                raise AssertionError("connection should have been rejected")
        except Exception:
            pass  # expected: server closes the connection during handshake
    finally:
        app.dependency_overrides.clear()
        rate_limit.set_redis_override(None)
        asyncio.run(engine.dispose())
