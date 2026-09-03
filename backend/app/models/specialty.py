from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Specialty(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "specialties"

    name_en: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    name_ar: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
