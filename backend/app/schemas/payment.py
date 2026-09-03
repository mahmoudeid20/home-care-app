import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.payment import PaymentStatus


class PaymentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: str | None
    transaction_id: str | None
    platform_commission: float
    nurse_earnings: float
    created_at: datetime

    model_config = {"from_attributes": True}


class MarkPaidRequest(BaseModel):
    payment_method: str = Field(
        min_length=1, max_length=50, description="e.g. 'cash', 'bank_transfer'"
    )
    transaction_id: str | None = Field(default=None, max_length=200)
