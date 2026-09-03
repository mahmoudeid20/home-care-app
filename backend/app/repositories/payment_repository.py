import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment, PaymentStatus


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **fields) -> Payment:
        payment = Payment(**fields)
        self.db.add(payment)
        await self.db.flush()
        await self.db.refresh(payment, attribute_names=["created_at", "updated_at"])
        return payment

    async def get_by_id(self, payment_id: uuid.UUID) -> Payment | None:
        return await self.db.get(Payment, payment_id)

    async def get_by_booking_id(self, booking_id: uuid.UUID) -> Payment | None:
        result = await self.db.execute(select(Payment).where(Payment.booking_id == booking_id))
        return result.scalar_one_or_none()

    async def list_all(
        self, status: PaymentStatus | None = None, limit: int = 20, offset: int = 0
    ) -> list[Payment]:
        stmt = select(Payment)
        if status is not None:
            stmt = stmt.where(Payment.status == status)
        stmt = stmt.order_by(Payment.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_status(
        self,
        payment: Payment,
        status: PaymentStatus,
        payment_method: str | None = None,
        transaction_id: str | None = None,
    ) -> None:
        payment.status = status
        if payment_method is not None:
            payment.payment_method = payment_method
        if transaction_id is not None:
            payment.transaction_id = transaction_id
        await self.db.flush()

    async def sum_paid_amount(self) -> float:
        result = await self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.PAID
            )
        )
        return float(result.scalar_one())

    async def sum_paid_commission(self) -> float:
        result = await self.db.execute(
            select(func.coalesce(func.sum(Payment.platform_commission), 0)).where(
                Payment.status == PaymentStatus.PAID
            )
        )
        return float(result.scalar_one())
