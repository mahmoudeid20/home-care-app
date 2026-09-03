"""
An Application is a care request sent to one specific nurse (Section 11:
"Send service requests to nurses" / Section 17-18: nurse receives/accepts/
rejects requests). When a nurse accepts, a Booking is created (Phase 5,
Section 45's flow: "nurse accepts -> booking is created").

Multiple nurses can have pending applications for the same care request
simultaneously (the patient may message several matched nurses); accepting
one automatically rejects the others for that same care request — see
ApplicationService.accept().
"""
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ApplicationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class Application(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "applications"
    __table_args__ = (
        # A patient can only have one *active* (non-terminal) application to
        # the same nurse for the same care request at a time. Terminal
        # statuses (REJECTED/WITHDRAWN) are excluded from this constraint at
        # the application-service layer (re-applying after a rejection is
        # allowed), so this DB constraint intentionally stays loose and the
        # real duplicate-prevention logic lives in ApplicationService.
    )

    care_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("care_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nurse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nurses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.PENDING,
        nullable=False,
        index=True,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    care_request = relationship("CareRequest", foreign_keys=[care_request_id])
    nurse = relationship("Nurse", foreign_keys=[nurse_id])
    patient = relationship("Patient", foreign_keys=[patient_id])
