"""
Database engine & session management (async SQLAlchemy 2.0).

Supports both PostgreSQL (production) and SQLite (local development).
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def _get_normalized_db_url(url: str) -> str:
    """Ensure cloud PostgreSQL connection strings are properly formatted for asyncpg."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # asyncpg expects ssl=require rather than sslmode=require
    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")
    return url

_db_url = _get_normalized_db_url(settings.DATABASE_URL)
_is_sqlite = _db_url.startswith("sqlite")

# SQLite needs special args: check_same_thread=False and StaticPool for async
if _is_sqlite:
    engine = create_async_engine(
        _db_url,
        echo=settings.DEBUG,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_async_engine(
        _db_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        future=True,
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
