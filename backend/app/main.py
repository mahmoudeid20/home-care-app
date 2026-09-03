"""
HomeCare API — application entrypoint.

Phase 1 wires up: config, DB, exception handling, CORS, and the auth router.
Later phases add routers under app/api/<domain>/router.py and include them
here — the wiring pattern stays the same for every domain.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.admin.router import router as admin_router
from app.api.applications.router import router as applications_router
from app.api.auth.router import router as auth_router
from app.api.bookings.router import router as bookings_router
from app.api.care_requests.router import router as care_requests_router
from app.api.complaints.router import router as complaints_router
from app.api.conversations.router import router as conversations_router
from app.api.lookup.router import router as lookup_router
from app.api.nurses.router import router as nurses_router
from app.api.notifications.router import router as notifications_router
from app.api.patients.router import router as patients_router
from app.api.payments.router import router as payments_router
from app.api.reviews.router import router as reviews_router
from app.api.uploads.router import router as uploads_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.websocket.chat_ws import router as chat_ws_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "HomeCare — home-care nursing marketplace API. "
            "AI functionality is limited to requirement extraction, matching, "
            "search, ranking, and administrative automation. It never provides "
            "medical diagnosis, prescriptions, or treatment recommendations."
        ),
        version="0.1.0",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    )

    # Middleware order matters: Starlette wraps outer-to-inner in the
    # *reverse* of add_middleware() call order (the last one added is
    # outermost). RateLimitMiddleware is added first (innermost) so that
    # SecurityHeadersMiddleware — added after it — still wraps and
    # decorates a 429 rate-limit response with the security headers,
    # rather than skipping them when RateLimitMiddleware short-circuits.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # A wildcard origin ("*") combined with allow_credentials=True is both
    # rejected by browsers and a real security footgun (it would let any
    # site read authenticated responses via CORS) — only enable credentials
    # once real origins are configured (Section 32: "CORS configuration").
    cors_allows_credentials = settings.CORS_ORIGINS != ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=cors_allows_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Consistent error response shape across the whole API (Section 37) ---
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.error_code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Pydantic v2 includes a raw exception object in `ctx` for errors raised
        # by custom @field_validator functions, which is not JSON-serializable.
        # Strip it while keeping the human-readable message.
        safe_errors = []
        for err in exc.errors():
            err = dict(err)
            err.pop("ctx", None)
            safe_errors.append(err)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": safe_errors,
                }
            },
        )

    @app.get("/health", tags=["System"], summary="Liveness/readiness probe")
    async def health() -> dict:
        return {"status": "ok", "env": settings.ENV}

    app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    app.include_router(patients_router, prefix=settings.API_V1_PREFIX)
    app.include_router(nurses_router, prefix=settings.API_V1_PREFIX)
    app.include_router(care_requests_router, prefix=settings.API_V1_PREFIX)
    app.include_router(applications_router, prefix=settings.API_V1_PREFIX)
    app.include_router(bookings_router, prefix=settings.API_V1_PREFIX)
    app.include_router(conversations_router, prefix=settings.API_V1_PREFIX)
    app.include_router(reviews_router, prefix=settings.API_V1_PREFIX)
    app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
    app.include_router(complaints_router, prefix=settings.API_V1_PREFIX)
    app.include_router(payments_router, prefix=settings.API_V1_PREFIX)
    app.include_router(lookup_router, prefix=settings.API_V1_PREFIX)
    app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
    app.include_router(uploads_router, prefix=settings.API_V1_PREFIX)
    app.include_router(chat_ws_router)  # no /api/v1 prefix — WS path is /ws/...

    return app


app = create_app()


@app.on_event("startup")
async def _create_tables():
    """Auto-create tables on startup so cloud deployment works immediately without manual migrations."""
    from app.core.database import engine, Base
    from app import models  # noqa: F401 — ensure all models are registered
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        import logging
        logging.getLogger("uvicorn").error(f"Error creating tables on startup: {e}")


# Serve uploaded files statically
_uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
_uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")
