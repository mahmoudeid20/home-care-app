import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.payment import PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/bookings", tags=["Payments"])


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


@router.get(
    "/{booking_id}/payment",
    response_model=PaymentResponse,
    summary="Get the payment for a booking (patient or nurse party only)",
    description=(
        "A payment record only exists once the booking has been COMPLETED "
        "(Section 30). Status starts PENDING until an admin marks it paid."
    ),
    responses={
        403: {"description": "Not your booking"},
        404: {"description": "Booking not found, or no payment yet"},
    },
)
async def get_booking_payment(
    booking_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    payment = await service.get_for_booking(user.id, booking_id)
    return PaymentResponse.model_validate(payment)
