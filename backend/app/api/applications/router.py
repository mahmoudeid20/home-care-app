import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRejectRequest,
    ApplicationResponse,
)
from app.schemas.booking import BookingResponse, booking_to_response
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])


def get_application_service(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(db)


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a care request to a specific nurse (Section 11)",
    description=(
        "PATIENT role only. The care request must be OPEN and owned by the "
        "caller; the nurse must be approved and not suspended."
    ),
    responses={
        404: {"description": "Care request or nurse not found, or no patient profile yet"},
        409: {"description": "A pending request to this nurse for this care request already exists"},
        422: {"description": "Care request not open, or nurse not currently accepting requests"},
    },
)
async def send_application(
    payload: ApplicationCreate,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    app_ = await service.create(user.id, payload)
    return ApplicationResponse.model_validate(app_)


@router.get(
    "/received",
    response_model=list[ApplicationResponse],
    summary="List requests received by the current nurse (Section 18 'New Requests')",
)
async def list_received_applications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: ApplicationService = Depends(get_application_service),
) -> list[ApplicationResponse]:
    items = await service.list_received(user.id, limit=limit, offset=offset)
    return [ApplicationResponse.model_validate(a) for a in items]


@router.get(
    "/sent",
    response_model=list[ApplicationResponse],
    summary="List requests the current patient has sent",
)
async def list_sent_applications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: ApplicationService = Depends(get_application_service),
) -> list[ApplicationResponse]:
    items = await service.list_sent(user.id, limit=limit, offset=offset)
    return [ApplicationResponse.model_validate(a) for a in items]


@router.post(
    "/{application_id}/accept",
    response_model=BookingResponse,
    summary="Accept a request — creates a booking (Section 45)",
    description=(
        "NURSE role only, owner only. Accepting moves the application to "
        "ACCEPTED, creates a Booking, sets the care request to MATCHED, and "
        "auto-rejects any other still-pending applications for the same "
        "care request."
    ),
    responses={
        403: {"description": "Not your application"},
        404: {"description": "Application not found"},
        422: {"description": "Application not PENDING, or care request no longer OPEN"},
    },
)
async def accept_application(
    application_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: ApplicationService = Depends(get_application_service),
) -> BookingResponse:
    _app, booking = await service.accept(user.id, application_id)
    return booking_to_response(booking)


@router.post(
    "/{application_id}/reject",
    response_model=ApplicationResponse,
    summary="Reject a request",
    responses={
        403: {"description": "Not your application"},
        404: {"description": "Application not found"},
        422: {"description": "Application not PENDING"},
    },
)
async def reject_application(
    application_id: uuid.UUID,
    payload: ApplicationRejectRequest,
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    app_ = await service.reject(user.id, application_id, payload.reason)
    return ApplicationResponse.model_validate(app_)


@router.post(
    "/{application_id}/withdraw",
    response_model=ApplicationResponse,
    summary="Withdraw a request before the nurse responds",
    responses={
        403: {"description": "Not your application"},
        404: {"description": "Application not found"},
        422: {"description": "Application not PENDING"},
    },
)
async def withdraw_application(
    application_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    app_ = await service.withdraw(user.id, application_id)
    return ApplicationResponse.model_validate(app_)
