import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.user import UserRole


class UserAdminResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str | None
    role: UserRole
    is_active: bool
    is_email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentReviewRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class NurseApprovalResponse(BaseModel):
    id: uuid.UUID
    is_approved: bool
    is_suspended: bool
    identity_verified: bool
    qualification_verified: bool
    experience_verified: bool

    model_config = {"from_attributes": True}


class ServiceUpsertRequest(BaseModel):
    name_en: str = Field(min_length=1, max_length=150)
    name_ar: str = Field(min_length=1, max_length=150)
    is_active: bool = True


class SpecialtyUpsertRequest(BaseModel):
    name_en: str = Field(min_length=1, max_length=150)
    name_ar: str = Field(min_length=1, max_length=150)
    is_active: bool = True


class PlatformSettingsResponse(BaseModel):
    commission_percentage: float

    model_config = {"from_attributes": True}


class PlatformSettingsUpdate(BaseModel):
    commission_percentage: float = Field(ge=0, le=1)


class AdminActionResponse(BaseModel):
    id: uuid.UUID
    admin_id: uuid.UUID
    action_type: str
    target_type: str
    target_id: uuid.UUID
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlatformStatsResponse(BaseModel):
    total_patients: int
    total_nurses: int
    verified_nurses: int
    pending_verifications: int
    active_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    total_revenue: float
    platform_commission_earned: float
    average_rating: float
    most_requested_services: list[dict] = Field(default_factory=list)
