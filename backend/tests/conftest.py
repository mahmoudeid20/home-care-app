"""
Test fixtures.

Uses an in-memory SQLite DB (via aiosqlite) instead of Postgres so the auth
test suite runs fast and without external services. A minimal fake Redis
(in-memory dict) replaces the real Redis client for the same reason.

Note: SQLite doesn't support the Postgres ENUM/UUID types natively at the
DDL level the way Postgres does, but SQLAlchemy's generic UUID/Enum types
degrade gracefully to CHAR/VARCHAR on SQLite, so `Base.metadata.create_all`
works fine for test purposes. Production migrations always target Postgres
via Alembic (migrations/versions/0001_create_users_table.py).
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.api.deps import get_redis_dep
from app.core import rate_limit
from app.main import app
from app import models  # noqa: F401  ensure models are registered
from app.models.service import Service
from app.models.specialty import Specialty


class FakeRedis:
    """Minimal async-compatible in-memory stand-in for redis.asyncio.Redis."""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex=None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def incr(self, key: str) -> int:
        current = int(self._store.get(key, "0"))
        current += 1
        self._store[key] = str(current)
        return current

    async def expire(self, key: str, seconds: int) -> None:
        # No-op: this fake has no real expiry, which is fine for tests —
        # each test gets a fresh FakeRedis instance via function-scoped
        # fixtures, so there's no cross-test key pollution to worry about.
        pass


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest_asyncio.fixture
async def client(db_session, fake_redis) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_dep] = override_get_redis
    # RateLimitMiddleware lives outside FastAPI's DI graph (it's Starlette
    # middleware, not a Depends()), so it can't be swapped via
    # dependency_overrides — point it at the same fake Redis instance
    # directly instead (see app/core/rate_limit.py).
    rate_limit.set_redis_override(fake_redis)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    rate_limit.set_redis_override(None)


@pytest_asyncio.fixture
async def seed_lookup(db_session) -> dict:
    """Seed a couple of specialties/services so nurse-profile tests have
    valid ids to reference (nurse creation validates ids against the DB)."""
    elderly = Specialty(name_en="Elderly Care", name_ar="رعاية المسنين")
    wound = Specialty(name_en="Wound Care", name_ar="رعاية الجروح")
    general = Service(name_en="General Nursing", name_ar="تمريض عام")
    db_session.add_all([elderly, wound, general])
    await db_session.commit()
    await db_session.refresh(elderly)
    await db_session.refresh(wound)
    await db_session.refresh(general)
    return {
        "specialty_elderly": elderly.id,
        "specialty_wound": wound.id,
        "service_general": general.id,
    }


async def register_and_get_token(client, email: str, role: str, password: str = "Passw0rd1") -> str:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["tokens"]["access_token"]
