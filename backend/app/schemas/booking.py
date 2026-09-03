import uuid
from datetime import date

from pydantic import BaseModel

from app.models.booking import BookingStatus
from app.models.nurse import PriceUnit


class BookingResponse(BaseModel):
    id: uuid.UUID
    care_request_id: uuid.UUID
    application_id: uuid.UUID
    patient_id: uuid.UUID
    nurse_id: uuid.UUID
    status: BookingStatus

    start_date: date
    end_date: date | None
    hours_per_day: float | None
    payment_frequency: PriceUnit
    agreed_price: float | None

    model_config = {"from_attributes": True}


def booking_to_response(booking) -> "BookingResponse":
    return BookingResponse(
        id=booking.id,
        care_request_id=booking.care_request_id,
        application_id=booking.application_id,
        patient_id=booking.patient_id,
        nurse_id=booking.nurse_id,
        status=booking.status,
        start_date=booking.start_date,
        end_date=booking.end_date,
        hours_per_day=float(booking.hours_per_day) if booking.hours_per_day is not None else None,
        payment_frequency=booking.payment_frequency,
        agreed_price=float(booking.agreed_price) if booking.agreed_price is not None else None,
    )
