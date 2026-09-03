"""
Rate limiting (Section 32). Fixed-window counter keyed by client identity
(authenticated user id when available, otherwise IP address), backed by
Redis INCR+EXPIRE -- atomic in real Redis, which is what matters in
production; the in-memory FakeRedis used in tests approximates this
closely enough for deterministic test behavior since each test gets a
fresh instance.

Deliberately reads settings.RATE_LIMIT_PER_MINUTE at call time (not once
at import time) so it can be adjusted per-environment without a restart,
and so tests can monkeypatch it directly.

Testability note: this middleware sits outside FastAPI's dependency-
injection graph (Starlette middleware, not a Depends()), so it can't use
the app.dependency_overrides mechanism the rest of the app's tests rely on
for Redis. Instead it goes through get_redis_client_for_rate_limit(),
which tests point at the same FakeRedis instance via set_redis_override()
(see tests/conftest.py) rather than hitting a real Redis connection.
"""
from app.core.config import settings
from app.core.redis import get_redis_client

_redis_override = None


def set_redis_override(client) -> None:
    """Test hook — see module docstring."""
    global _redis_override
    _redis_override = client


def get_redis_client_for_rate_limit():
    return _redis_override if _redis_override is not None else get_redis_client()


WINDOW_SECONDS = 60


async def is_rate_limited(identifier: str) -> tuple[bool, int]:
    """Returns (is_limited, current_count). Fails open if Redis is unavailable."""
    try:
        redis = get_redis_client_for_rate_limit()
        key = f"ratelimit:{identifier}"

        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, WINDOW_SECONDS)

        limit = settings.RATE_LIMIT_PER_MINUTE
        return count > limit, count
    except Exception:
        # Redis unavailable — fail open (allow the request)
        return False, 0
