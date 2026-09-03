"""
Redis connection. Used for:
- Refresh-token blacklist (logout / rotation, Section 32)
- Rate limiting (Phase 9)
- Future: caching search/matching results
"""
from redis.asyncio import Redis, from_url

from app.core.config import settings

_redis: Redis | None = None


def get_redis_client() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def get_redis() -> Redis:
    """FastAPI dependency."""
    return get_redis_client()
