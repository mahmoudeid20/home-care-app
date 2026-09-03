"""
Nurse professional profile and everything attached to nurse onboarding
(Section 17): specialties, priced services, availability, and identity/
qualification documents with an admin review status.

Verification badges (Section 16) must only ever be derived from
`identity_verified` / `qualification_verified` / `experience_verified` —
never inferred client-side — and a nurse cannot receive requests until
`is_approved` is set by an admin (Phase 8).
"""
import enum
import uuid
from datetime import date, time

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class PriceUnit(str, enum.Enum):
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class ShiftType(str, enum.Enum):
    MORNING = "MORNING"
    EVENING = "EVENING"
    NIGHT = "NIGHT"
    HOURS_24 = "HOURS_24"
    CUSTOM = "CUSTOM"


class DocumentType(str, enum.Enum):
    NATIONAL_ID = "NATIONAL_ID"
    NATIONAL_ID_FRONT = "NATIONAL_ID_FRONT"
    NATIONAL_ID_BACK = "NATIONAL_ID_BACK"
    NURSING_CERTIFICATE = "NURSING_CERTIFICATE"
    GRADUATION_CERTIFICATE = "GRADUATION_CERTIFICATE"
    EXPERIENCE_CERTIFICATE = "EXPERIENCE_CERTIFICATE"
    OTHER = "OTHER"


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Nurse(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "nurses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    professional_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    # URL of an already-uploaded image in secure object storage (Section 32
    # pattern — same as nurse_documents.file_url). Nothing here handles raw
    # bytes; the mobile/admin client uploads first, then sends the URL.
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, name="nurse_gender"), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    experience_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    education: Mapped[str | None] = mapped_column(Text, nullable=True)

    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    # --- Verification (Section 16/17/28) ---
    identity_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    qualification_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    experience_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Overall gate: nurse cannot receive/accept requests until an admin approves.
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- Denormalized aggregates for fast search/display, recomputed by
    # the review service (Phase 7) whenever a review is created. ---
    average_rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    location = relationship("Location", foreign_keys=[location_id])
    specialties = relationship(
        "NurseSpecialty", back_populates="nurse", cascade="all, delete-orphan"
    )
    services = relationship("NurseService", back_populates="nurse", cascade="all, delete-orphan")
    availability_slots = relationship(
        "NurseAvailability", back_populates="nurse", cascade="all, delete-orphan"
    )
    documents = relationship("NurseDocument", back_populates="nurse", cascade="all, delete-orphan")

    @property
    def is_fully_verified(self) -> bool:
        return self.identity_verified and self.qualification_verified and self.experience_verified


class NurseSpecialty(Base):
    __tablename__ = "nurse_specialties"
    __table_args__ = (UniqueConstraint("nurse_id", "specialty_id", name="uq_nurse_specialty"),)

    nurse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nurses.id", ondelete="CASCADE"), primary_key=True
    )
    specialty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specialties.id", ondelete="CASCADE"), primary_key=True
    )

    nurse = relationship("Nurse", back_populates="specialties")
    specialty = relationship("Specialty")


class NurseService(Base):
    __tablename__ = "nurse_services"
    __table_args__ = (UniqueConstraint("nurse_id", "service_id", name="uq_nurse_service"),)

    nurse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nurses.id", ondelete="CASCADE"), primary_key=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), primary_key=True
    )
    # Prices are always numeric — never formatted strings (Section 13).
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_unit: Mapped[PriceUnit] = mapped_column(Enum(PriceUnit, name="price_unit"), nullable=False)

    nurse = relationship("Nurse", back_populates="services")
    service = relationship("Service")


class NurseAvailability(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "nurse_availability"

    nurse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 0=Monday ... 6=Sunday. NULL day_of_week + shift_type=CUSTOM means the
    # nurse indicated general/flexible availability without a fixed weekly slot.
    day_of_week: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    shift_type: Mapped[ShiftType] = mapped_column(Enum(ShiftType, name="shift_type"), nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    nurse = relationship("Nurse", back_populates="availability_slots")


class NurseDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "nurse_documents"

    nurse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"), nullable=False
    )
    # Points at secure object storage (Section 32: secure file storage) —
    # never a publicly-guessable URL. Signed-URL generation is a storage-
    # integration concern outside this model.
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    nurse = relationship("Nurse", back_populates="documents")
