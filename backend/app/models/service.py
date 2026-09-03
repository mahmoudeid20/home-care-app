from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Service(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Configurable service catalog (General Nursing, Elderly Care, Wound Care,
    ...). Must be editable from the admin dashboard (Phase 8) rather than
    hard-coded in the mobile app, per Section 9.
    """
    __tablename__ = "services"

    name_en: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    name_ar: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
