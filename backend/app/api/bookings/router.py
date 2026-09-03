import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.booking import BookingResponse, booking_to_response
from app.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    return BookingService(db)


@router.get(
    "",
    response_model=list[BookingResponse],
    summary="List the current user's bookings (patient or nurse)",
)
async def list_my_bookings(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: BookingService = Depends(get_booking_service),
) -> list[BookingResponse]:
    items = await service.list_mine(user.id, limit=limit, offset=offset)
    return [booking_to_response(b) for b in items]


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get a booking (patient or nurse party only)",
    responses={403: {"description": "Not your booking"}, 404: {"description": "Not found"}},
)
async def get_booking(
    booking_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    booking = await service.get(user.id, booking_id)
    return booking_to_response(booking)


@router.post(
    "/{booking_id}/confirm",
    response_model=BookingResponse,
    summary="Confirm a booking (PATIENT only, ACCEPTED -> CONFIRMED)",
    responses={
        403: {"description": "Not your booking, or wrong role for this action"},
        404: {"description": "Not found"},
        422: {"description": "Not a legal transition from the current status"},
    },
)
async def confirm_booking(
    booking_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    booking = await service.confirm(user.id, booking_id)
    return booking_to_response(booking)


@router.post(
    "/{booking_id}/start",
    response_model=BookingResponse,
    summary="Mark care as started (NURSE only, CONFIRMED -> ACTIVE)",
    responses={
        403: {"description": "Not your booking, or wrong role for this action"},
        404: {"description": "Not found"},
        422: {"description": "Not a legal transition from the current status"},
    },
)
async def start_booking(
    booking_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    booking = await service.start(user.id, booking_id)
    return booking_to_response(booking)


@router.post(
    "/{booking_id}/complete",
    response_model=BookingResponse,
    summary="Mark care as completed (NURSE only, ACTIVE -> COMPLETED)",
    responses={
        403: {"description": "Not your booking, or wrong role for this action"},
        404: {"description": "Not found"},
        422: {"description": "Not a legal transition from the current status"},
    },
)
async def complete_booking(
    booking_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    booking = await service.complete(user.id, booking_id)
    return booking_to_response(booking)


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
    summary="Cancel a booking (either party, only from ACCEPTED/CONFIRMED)",
    description="Reopens the underlying care request to OPEN so the patient can look for another nurse.",
    responses={
        403: {"description": "Not your booking"},
        404: {"description": "Not found"},
        422: {"description": "Not a legal transition from the current status"},
    },
)
async def cancel_booking(
    booking_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    booking = await service.cancel(user.id, booking_id)
    return booking_to_response(booking)
