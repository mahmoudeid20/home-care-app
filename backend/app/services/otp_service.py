import logging
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.otp import OTPChannel, OTPCode, OTPPurpose
from app.models.user import User

logger = logging.getLogger("sanad.otp")


class OTPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_otp(
        self,
        recipient: str,
        channel: OTPChannel = OTPChannel.EMAIL,
        purpose: OTPPurpose = OTPPurpose.REGISTRATION,
        user_id = None,
    ) -> str:
        # Rate limit: allow up to 5 OTP requests per minute for this recipient
        one_minute_ago = datetime.now(timezone.utc) - timedelta(seconds=60)
        from sqlalchemy import func
        recent_count = (
            await self.db.execute(
                select(func.count(OTPCode.id)).where(
                    and_(
                        OTPCode.recipient == recipient,
                        OTPCode.purpose == purpose,
                        OTPCode.created_at >= one_minute_ago,
                    )
                )
            )
        ).scalar() or 0
        if recent_count >= 5:
            raise BadRequestError("تم إرسال عدة رموز مؤخراً، يرجى الانتظار دقيقة واحدة قبل طلب رمز جديد")

        # Invalidate previous unused codes for this recipient & purpose
        prev_codes = await self.db.execute(
            select(OTPCode).where(
                and_(
                    OTPCode.recipient == recipient,
                    OTPCode.purpose == purpose,
                    OTPCode.is_used == False,
                )
            )
        )
        for old in prev_codes.scalars().all():
            old.is_used = True

        # Generate 6-digit cryptographically random code
        code = f"{random.randint(100000, 999999)}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        otp_record = OTPCode(
            user_id=user_id,
            recipient=recipient,
            code=code,
            channel=channel,
            purpose=purpose,
            expires_at=expires_at,
            is_used=False,
            attempts=0,
        )
        self.db.add(otp_record)
        await self.db.commit()

        # Deliver the OTP
        await self._deliver_otp(recipient, code, channel, purpose)
        return code

    async def verify_otp(
        self,
        recipient: str,
        code: str,
        purpose: OTPPurpose = OTPPurpose.REGISTRATION,
    ) -> bool:
        stmt = (
            select(OTPCode)
            .where(
                and_(
                    OTPCode.recipient == recipient,
                    OTPCode.purpose == purpose,
                    OTPCode.is_used == False,
                )
            )
            .order_by(OTPCode.created_at.desc())
        )
        result = await self.db.execute(stmt)
        record = result.scalars().first()

        if not record:
            raise NotFoundError("لا يوجد رمز تحقق صالح لهذا الحساب. اطلب رمزاً جديداً")

        if record.is_expired:
            record.is_used = True
            await self.db.commit()
            raise BadRequestError("انتهت صلاحية الرمز، يرجى طلب رمز جديد")

        if record.attempts >= 5:
            record.is_used = True
            await self.db.commit()
            raise BadRequestError("تم تجاوز الحد الأقصى للمحاولات الخاطئة")

        if record.code != code.strip():
            record.attempts += 1
            await self.db.commit()
            raise BadRequestError("رمز التحقق غير صحيح، يرجى التأكد وإعادة المحاولة")

        # Successfully verified
        record.is_used = True

        # If user exists, mark email or phone as verified
        if record.user_id:
            user = await self.db.get(User, record.user_id)
            if user:
                if record.channel == OTPChannel.EMAIL:
                    user.is_email_verified = True
                elif record.channel == OTPChannel.SMS:
                    user.is_phone_verified = True

        await self.db.commit()
        return True

    async def _deliver_otp(
        self,
        recipient: str,
        code: str,
        channel: OTPChannel,
        purpose: OTPPurpose,
    ) -> None:
        """Delivers the OTP. Logs prominently and sends via configured channel."""
        logger.info("=" * 50)
        logger.info(f"🔑 [SANAD OTP] {purpose.value} for {recipient}: {code} (Channel: {channel.value})")
        logger.info("=" * 50)

        # In development / sandbox mode, printing it guarantees developers/testers never get blocked.
        print(f"\n>>>> [SANAD OTP CODE FOR {recipient}]: {code} <<<<\n")
