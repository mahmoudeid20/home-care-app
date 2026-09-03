"""
Import every ORM model here so Alembic's `target_metadata` (Base.metadata)
sees the full schema when autogenerating migrations. As new phases add
models (patients, nurses, care_requests, ...), import them here too.
"""
from app.models.user import User, UserRole  # noqa: F401
from app.models.location import Location  # noqa: F401
from app.models.specialty import Specialty  # noqa: F401
from app.models.service import Service  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.nurse import (  # noqa: F401
    DocumentStatus,
    DocumentType,
    Gender,
    Nurse,
    NurseAvailability,
    NurseDocument,
    NurseService,
    NurseSpecialty,
    PriceUnit,
    ShiftType,
)
from app.models.care_request import (  # noqa: F401
    CareRequest,
    CareRequestRequirement,
    CareRequestService,
    CareRequestSpecialty,
    CareRequestStatus,
    MobilityStatus,
)
from app.models.matching_weight import MatchingWeights  # noqa: F401
from app.models.application import Application, ApplicationStatus  # noqa: F401
from app.models.booking import Booking, BookingStatus  # noqa: F401
from app.models.conversation import Conversation, Message, MessageType  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.notification import Notification, NotificationType  # noqa: F401
from app.models.admin_action import AdminAction  # noqa: F401
from app.models.platform_settings import PlatformSettings  # noqa: F401
from app.models.payment import Payment, PaymentStatus  # noqa: F401
from app.models.complaint import Complaint, ComplaintStatus  # noqa: F401
from app.models.otp import OTPCode, OTPChannel, OTPPurpose  # noqa: F401

__all__ = [
    "User",
    "UserRole",
    "Location",
    "Specialty",
    "Service",
    "Patient",
    "Nurse",
    "NurseSpecialty",
    "NurseService",
    "NurseAvailability",
    "NurseDocument",
    "Gender",
    "PriceUnit",
    "ShiftType",
    "DocumentType",
    "DocumentStatus",
    "CareRequest",
    "CareRequestService",
    "CareRequestSpecialty",
    "CareRequestRequirement",
    "CareRequestStatus",
    "MobilityStatus",
    "MatchingWeights",
    "Application",
    "ApplicationStatus",
    "Booking",
    "BookingStatus",
    "Conversation",
    "Message",
    "MessageType",
    "Review",
    "Notification",
    "NotificationType",
    "AdminAction",
    "PlatformSettings",
    "Payment",
    "PaymentStatus",
    "Complaint",
    "ComplaintStatus",
]
