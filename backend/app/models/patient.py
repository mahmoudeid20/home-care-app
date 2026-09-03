"""
`patients` is the profile of the *account holder* (the person managing
care — themselves or a family member), per Section 8's onboarding flow
("Create a patient profile"). Details about the specific person who needs
care (name, age, medical condition — Section 9 Step 1) are captured on each
`care_request` in Phase 3, since one account holder may create requests for
different family members over time.
"""
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Patient(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "patients"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    national_id: Mapped[str | None] = mapped_column(String(14), unique=True, index=True, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    preferred_language: Mapped[str] = mapped_column(String(5), default="ar", nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    location = relationship("Location", foreign_keys=[location_id])
