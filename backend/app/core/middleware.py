"""
Two Starlette middlewares implementing the remaining items from Section
32's security checklist that aren't naturally per-endpoint concerns:
rate limiting and secure HTTP headers.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.rate_limit import is_rate_limited
from app.core.security import decode_token

# Health checks and interactive docs are exempt — they're not user actions
# and rate-limiting them would just break monitoring/tooling.
_RATE_LIMIT_EXEMPT_PREFIXES = ("/health", "/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith(_RATE_LIMIT_EXEMPT_PREFIXES):
            return await call_next(request)

        identifier = await self._identify(request)
        limited, count = await is_rate_limited(identifier)
        if limited:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Please slow down and try again shortly.",
                    }
                },
                headers={"Retry-After": "60"},
            )
        return await call_next(request)

    async def _identify(self, request: Request) -> str:
        """Prefer the authenticated user id (fairer — one heavy user
        doesn't block others behind the same NAT/proxy IP); fall back to
        client IP for unauthenticated requests."""
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token, token_type="access")
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
            except Exception:
                pass

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Conservative defaults for a JSON API (Section 32: "Secure HTTP
    headers"). No CSP script-src/style-src rules are needed since this
    service never returns HTML, but the headers below still matter for any
    browser that ends up rendering an error page or a misconfigured proxy
    response.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response
