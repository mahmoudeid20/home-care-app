"""
Single-row platform configuration, same pattern as MatchingWeights.
Currently holds the commission percentage (Section 31: "The commission
percentage must be configurable by the administrator").
"""
from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PlatformSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "platform_settings"

    # Fraction, e.g. 0.10 = 10%.
    commission_percentage: Mapped[float] = mapped_column(Numeric(4, 3), default=0.10, nullable=False)
