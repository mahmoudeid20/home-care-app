"""
Shared location reference. Kept as its own table (per Section 5's required
`locations` entity) so patients, nurses, and later care_requests can all
reference structured location data consistently, and so admin can manage
supported governorates/cities centrally (Section 26).
"""
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Location(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "locations"

    governorate: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    area: Mapped[str | None] = mapped_column(String(150), nullable=True)
    address_line: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Nullable: not every location is pinned on a map yet.
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Location {self.governorate}/{self.city}>"
