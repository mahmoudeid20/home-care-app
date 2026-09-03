"""
Care request models — covers Sections 9-13 of the spec:
  Step 1: patient information (who needs care)
  Step 2: required care (services)
  Step 3: nurse requirements (gender/experience/specialties/languages/shift)
  Step 4: location
  Step 5: schedule
  Step 6: budget

Design notes:
- `patients` (Phase 2) is the *account holder's* profile. The person who
  actually needs care is described per-request here, since one account
  holder may create requests for different family members over time.
- `care_request_requirements` is kept as a generic key/value extension
  table (per Section 5's required entity) so Phase 10's AI requirement
  extraction can attach additional structured fields later without a
  schema migration every time a new extractable field is added.
- Reuses `PriceUnit` from nurse.py for `payment_frequency` — the same
  concept (hourly/daily/weekly/monthly) applies to both a nurse's listed
  price and a patient's requested payment frequency.
- Budget and hours are always numeric, never formatted strings (Section 13).
"""
import enum
import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.nurse import Gender, PriceUnit, ShiftType


class CareRequestStatus(str, enum.Enum):
    OPEN = "OPEN"          # published, visible for matching/applications
    MATCHED = "MATCHED"    # patient has accepted a nurse (booking created)
    CLOSED = "CLOSED"      # fulfilled and no longer accepting applications
    EXPIRED = "EXPIRED"    # start date passed with no booking
    CANCELLED = "CANCELLED"


class MobilityStatus(str, enum.Enum):
    INDEPENDENT = "INDEPENDENT"
    NEEDS_ASSISTANCE = "NEEDS_ASSISTANCE"
    WHEELCHAIR = "WHEELCHAIR"
    BEDRIDDEN = "BEDRIDDEN"


class CareRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "care_requests"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[CareRequestStatus] = mapped_column(
        Enum(CareRequestStatus, name="care_request_status"),
        default=CareRequestStatus.OPEN,
        nullable=False,
        index=True,
    )

    # --- Step 1: patient information (Section 9) ---
    patient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    patient_age: Mapped[int] = mapped_column(Integer, nullable=False)
    patient_gender: Mapped[Gender] = mapped_column(Enum(Gender, name="nurse_gender"), nullable=False)
    medical_condition: Mapped[str] = mapped_column(Text, nullable=False)
    mobility_status: Mapped[MobilityStatus] = mapped_column(
        Enum(MobilityStatus, name="mobility_status"), nullable=False
    )
    special_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Step 3: nurse requirements (Section 10) ---
    preferred_nurse_gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="nurse_gender"), nullable=True
    )
    min_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    languages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    verified_nurses_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_shift: Mapped[ShiftType] = mapped_column(
        Enum(ShiftType, name="shift_type"), default=ShiftType.CUSTOM, nullable=False
    )

    # --- Step 4: location (Section 11) ---
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    # --- Step 5: schedule (Section 12) ---
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    hours_per_day: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    number_of_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    custom_schedule_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_frequency: Mapped[PriceUnit] = mapped_column(Enum(PriceUnit, name="price_unit"), nullable=False)

    # --- Step 6: budget (Section 13) — numeric only, never a formatted string ---
    budget_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    location = relationship("Location", foreign_keys=[location_id])
    required_services = relationship(
        "CareRequestService", back_populates="care_request", cascade="all, delete-orphan"
    )
    required_specialties = relationship(
        "CareRequestSpecialty", back_populates="care_request", cascade="all, delete-orphan"
    )
    extra_requirements = relationship(
        "CareRequestRequirement", back_populates="care_request", cascade="all, delete-orphan"
    )


class CareRequestService(Base):
    """Join table: which services (Section 9 Step 2) are being requested."""
    __tablename__ = "care_request_services"

    care_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("care_requests.id", ondelete="CASCADE"), primary_key=True
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), primary_key=True
    )

    care_request = relationship("CareRequest", back_populates="required_services")
    service = relationship("Service")


class CareRequestSpecialty(Base):
    """Join table: required specialties (Section 10)."""
    __tablename__ = "care_request_specialties"

    care_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("care_requests.id", ondelete="CASCADE"), primary_key=True
    )
    specialty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specialties.id", ondelete="CASCADE"), primary_key=True
    )

    care_request = relationship("CareRequest", back_populates="required_specialties")
    specialty = relationship("Specialty")


class CareRequestRequirement(Base, UUIDPrimaryKeyMixin):
    """
    Generic key/value extension (Section 5's required `care_request_requirements`
    entity). Reserved for requirements that don't have a fixed column — e.g.
    additional structured fields produced by Phase 10's AI extraction.
    """
    __tablename__ = "care_request_requirements"

    care_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    care_request = relationship("CareRequest", back_populates="extra_requirements")
