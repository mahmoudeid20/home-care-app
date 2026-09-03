"""
Shared FastAPI dependencies: DB session, Redis, current-user extraction,
and role-based access guards (Section 6: RBAC).
"""
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")

    try:
        payload = decode_token(credentials.credentials, token_type="access")
    except JWTError:
        raise UnauthorizedError("Invalid or expired access token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token payload")

    user = await UserRepository(db).get_by_id(uuid.UUID(user_id))
    if not user or not user.is_active:
        raise UnauthorizedError("Account not found or inactive")

    return user


def require_roles(*allowed_roles: UserRole):
    """
    Usage: Depends(require_roles(UserRole.ADMIN))
    A patient must not access nurse/admin endpoints, a nurse must not access
    admin endpoints (Section 6) — this is enforced centrally here rather
    than being re-implemented per endpoint.
    """

    async def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise ForbiddenError(
                f"This action requires one of roles: {[r.value for r in allowed_roles]}"
            )
        return user

    return _guard


class _InMemoryRedis:
    """Minimal in-memory Redis stand-in for local dev without Redis."""

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
        pass


_fallback_redis = _InMemoryRedis()


async def get_redis_dep() -> Redis:
    try:
        client = await get_redis()
        await client.ping()
        return client
    except Exception:
        return _fallback_redis


def get_llm_client_dep():
    """FastAPI dependency wrapping get_llm_client() (Section 22's AI
    extraction). Defined as a real Depends() — not called directly inside
    a service constructor — specifically so tests can swap in a fake via
    app.dependency_overrides, the same pattern used for get_redis_dep."""
    from app.services.llm_client import get_llm_client

    return get_llm_client()
