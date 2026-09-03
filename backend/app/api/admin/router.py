"""
ADMIN-only endpoints (Sections 26-31): user management, nurse verification
with audit logging, catalog (services/specialties) management, platform
settings (matching weights, commission), payments oversight, complaint
triage, and dashboard statistics.
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.complaint import ComplaintStatus
from app.models.nurse import DocumentStatus
from app.models.payment import PaymentStatus
from app.models.user import User, UserRole
from app.repositories.matching_weight_repository import MatchingWeightsRepository
from app.repositories.platform_settings_repository import PlatformSettingsRepository
from app.schemas.admin import (
    AdminActionResponse,
    DocumentReviewRequest,
    NurseApprovalResponse,
    PlatformSettingsResponse,
    PlatformSettingsUpdate,
    PlatformStatsResponse,
    ServiceUpsertRequest,
    SpecialtyUpsertRequest,
    UserAdminResponse,
)
from app.schemas.complaint import ComplaintAdminUpdate, ComplaintResponse
from app.schemas.lookup import ServiceResponse, SpecialtyResponse
from app.schemas.matching import MatchingWeightsResponse, MatchingWeightsUpdate
from app.schemas.nurse import NurseDocumentResponse, nurse_to_response
from app.schemas.payment import MarkPaidRequest, PaymentResponse
from app.services.admin_catalog_service import AdminCatalogService
from app.services.admin_nurse_service import AdminNurseService
from app.services.admin_stats_service import AdminStatsService
from app.services.admin_user_service import AdminUserService
from app.services.complaint_service import ComplaintService
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/admin", tags=["Admin"])
_admin_only = require_roles(UserRole.ADMIN)


def get_weights_repo(db: AsyncSession = Depends(get_db)) -> MatchingWeightsRepository:
    return MatchingWeightsRepository(db)


def get_settings_repo(db: AsyncSession = Depends(get_db)) -> PlatformSettingsRepository:
    return PlatformSettingsRepository(db)


def get_admin_user_service(db: AsyncSession = Depends(get_db)) -> AdminUserService:
    return AdminUserService(db)


def get_admin_nurse_service(db: AsyncSession = Depends(get_db)) -> AdminNurseService:
    return AdminNurseService(db)


def get_admin_catalog_service(db: AsyncSession = Depends(get_db)) -> AdminCatalogService:
    return AdminCatalogService(db)


def get_admin_stats_service(db: AsyncSession = Depends(get_db)) -> AdminStatsService:
    return AdminStatsService(db)


def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


def get_complaint_service(db: AsyncSession = Depends(get_db)) -> ComplaintService:
    return ComplaintService(db)


# --- Matching weights (Section 21, carried over from Phase 4) ---


@router.get("/matching-weights", response_model=MatchingWeightsResponse, summary="Get the current matching engine weights")
async def get_matching_weights(
    user: User = Depends(_admin_only),
    repo: MatchingWeightsRepository = Depends(get_weights_repo),
) -> MatchingWeightsResponse:
    weights = await repo.get_active()
    return MatchingWeightsResponse.model_validate(weights)


@router.patch(
    "/matching-weights",
    response_model=MatchingWeightsResponse,
    summary="Update the matching engine weights",
    responses={422: {"description": "Weights do not sum to 1.0"}},
)
async def update_matching_weights(
    payload: MatchingWeightsUpdate,
    user: User = Depends(_admin_only),
    repo: MatchingWeightsRepository = Depends(get_weights_repo),
) -> MatchingWeightsResponse:
    current = await repo.get_active()
    updated = await repo.update(current, **payload.model_dump())
    return MatchingWeightsResponse.model_validate(updated)


# --- Platform settings: commission (Section 31) ---


@router.get("/settings", response_model=PlatformSettingsResponse, summary="Get platform settings (commission %)")
async def get_platform_settings(
    user: User = Depends(_admin_only),
    repo: PlatformSettingsRepository = Depends(get_settings_repo),
) -> PlatformSettingsResponse:
    settings = await repo.get_active()
    return PlatformSettingsResponse.model_validate(settings)


@router.patch("/settings", response_model=PlatformSettingsResponse, summary="Update the commission percentage")
async def update_platform_settings(
    payload: PlatformSettingsUpdate,
    user: User = Depends(_admin_only),
    repo: PlatformSettingsRepository = Depends(get_settings_repo),
) -> PlatformSettingsResponse:
    current = await repo.get_active()
    updated = await repo.update(current, payload.commission_percentage)
    return PlatformSettingsResponse.model_validate(updated)


# --- Users (Section 26) ---


@router.get("/users", response_model=list[UserAdminResponse], summary="List all users")
async def list_users(
    role: UserRole | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(_admin_only),
    service: AdminUserService = Depends(get_admin_user_service),
) -> list[UserAdminResponse]:
    users = await service.list_users(role=role, limit=limit, offset=offset)
    return [UserAdminResponse.model_validate(u) for u in users]


@router.post("/users/{user_id}/deactivate", response_model=UserAdminResponse, summary="Deactivate a user account")
async def deactivate_user(
    user_id: uuid.UUID,
    payload: DocumentReviewRequest,
    user: User = Depends(_admin_only),
    service: AdminUserService = Depends(get_admin_user_service),
) -> UserAdminResponse:
    target = await service.deactivate(user.id, user_id, payload.reason)
    return UserAdminResponse.model_validate(target)


@router.post("/users/{user_id}/activate", response_model=UserAdminResponse, summary="Reactivate a user account")
async def activate_user(
    user_id: uuid.UUID,
    user: User = Depends(_admin_only),
    service: AdminUserService = Depends(get_admin_user_service),
) -> UserAdminResponse:
    target = await service.activate(user.id, user_id)
    return UserAdminResponse.model_validate(target)


# --- Nurse verification (Section 17, 28) ---


@router.get("/nurses", summary="List nurses for verification review")
async def list_nurses_admin(
    is_approved: bool | None = None,
    pending_verification: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(_admin_only),
    service: AdminNurseService = Depends(get_admin_nurse_service),
):
    nurses = await service.list_nurses(
        is_approved=is_approved, pending_verification=pending_verification, limit=limit, offset=offset
    )
    return [nurse_to_response(n) for n in nurses]


@router.get(
    "/nurses/{nurse_id}/documents",
    response_model=list[NurseDocumentResponse],
    summary="View a nurse's uploaded documents",
)
async def get_nurse_documents_admin(
    nurse_id: uuid.UUID,
    user: User = Depends(_admin_only),
    service: AdminNurseService = Depends(get_admin_nurse_service),
) -> list[NurseDocumentResponse]:
    docs = await service.get_documents(nurse_id)
    return [NurseDocumentResponse.model_validate(d) for d in docs]


@router.post(
    "/nurses/{nurse_id}/documents/{document_id}/approve",
    response_model=NurseDocumentResponse,
    summary="Approve a nurse document — flips the matching verification flag",
)
async def approve_nurse_document(
    nurse_id: uuid.UUID,
    document_id: uuid.UUID,
    user: User = Depends(_admin_only),
    service: AdminNurseService = Depends(get_admin_nurse_service),
) -> NurseDocumentResponse:
    doc = await service.approve_document(user.id, nurse_id, document_id)
    return NurseDocumentResponse.model_validate(doc)


@router.post(
    "/nurses/{nurse_id}/documents/{document_id}/reject",
    response_model=NurseDocumentResponse,
    summary="Reject a nurse document",
)
async def reject_nurse_document(
    nurse_id: uuid.UUID,
    document_id: uuid.UUID,
    payload: DocumentReviewRequest,
    user: User = Depends(_admin_only),
    service: AdminNurseService = Depends(get_admin_nurse_service),
) -> NurseDocumentResponse:
    doc = await service.reject_document(user.id, nurse_id, document_id, payload.reason)
    return NurseDocumentResponse.model_validate(doc)


@router.post(
    "/nurses/{nurse_id}/approve",
    response_model=NurseApprovalResponse,
    summary="Approve a nurse (requires all three verification flags first)",
    responses={422: {"description": "Not all verification flags are true yet"}},
)
async def approve_nurse(
    nurse_id: uuid.UUID,
    user: User = Depends(_admin_only),
    service: AdminNurseService = Depends(get_admin_nurse_service),
) -> NurseApprovalResponse:
    nurse = await service.approve_nurse(user.id, nurse_id)
    return NurseApprovalResponse.model_validate(nurse)


@router.post("/nurses/{nurse_id}/suspend", response_model=NurseApprovalResponse, summary="Suspend a nurse")
async def suspend_nurse(
    nurse_id: uuid.UUID,
    payload: DocumentReviewRequest,
    user: User = Depends(_admin_only),
    service: AdminNurseService = Depends(get_admin_nurse_service),
) -> NurseApprovalResponse:
    nurse = await service.suspend_nurse(user.id, nurse_id, payload.reason)
    return NurseApprovalResponse.model_validate(nurse)


@router.post("/nurses/{nurse_id}/reactivate", response_model=NurseApprovalResponse, summary="Reactivate a suspended nurse")
async def reactivate_nurse(
    nurse_id: uuid.UUID,
    user: User = Depends(_admin_only),
    service: AdminNurseService = Depends(get_admin_nurse_service),
) -> NurseApprovalResponse:
    nurse = await service.reactivate_nurse(user.id, nurse_id)
    return NurseApprovalResponse.model_validate(nurse)


# --- Catalog: services & specialties (Section 9, 26) ---


@router.get("/services", response_model=list[ServiceResponse], summary="List all services, including inactive ones")
async def list_services_admin(
    user: User = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[ServiceResponse]:
    from app.repositories.lookup_repository import LookupRepository

    items = await LookupRepository(db).list_services(active_only=False)
    return [ServiceResponse.model_validate(i) for i in items]


@router.get(
    "/specialties", response_model=list[SpecialtyResponse], summary="List all specialties, including inactive ones"
)
async def list_specialties_admin(
    user: User = Depends(_admin_only),
    db: AsyncSession = Depends(get_db),
) -> list[SpecialtyResponse]:
    from app.repositories.lookup_repository import LookupRepository

    items = await LookupRepository(db).list_specialties(active_only=False)
    return [SpecialtyResponse.model_validate(i) for i in items]


@router.post("/services", response_model=ServiceResponse, summary="Create a service")
async def create_service(
    payload: ServiceUpsertRequest,
    user: User = Depends(_admin_only),
    service: AdminCatalogService = Depends(get_admin_catalog_service),
) -> ServiceResponse:
    return ServiceResponse.model_validate(await service.create_service(user.id, payload))


@router.patch("/services/{service_id}", response_model=ServiceResponse, summary="Update a service")
async def update_service(
    service_id: uuid.UUID,
    payload: ServiceUpsertRequest,
    user: User = Depends(_admin_only),
    service: AdminCatalogService = Depends(get_admin_catalog_service),
) -> ServiceResponse:
    return ServiceResponse.model_validate(await service.update_service(user.id, service_id, payload))


@router.post("/specialties", response_model=SpecialtyResponse, summary="Create a specialty")
async def create_specialty(
    payload: SpecialtyUpsertRequest,
    user: User = Depends(_admin_only),
    service: AdminCatalogService = Depends(get_admin_catalog_service),
) -> SpecialtyResponse:
    return SpecialtyResponse.model_validate(await service.create_specialty(user.id, payload))


@router.patch("/specialties/{specialty_id}", response_model=SpecialtyResponse, summary="Update a specialty")
async def update_specialty(
    specialty_id: uuid.UUID,
    payload: SpecialtyUpsertRequest,
    user: User = Depends(_admin_only),
    service: AdminCatalogService = Depends(get_admin_catalog_service),
) -> SpecialtyResponse:
    return SpecialtyResponse.model_validate(await service.update_specialty(user.id, specialty_id, payload))


# --- Payments (Section 30) ---


@router.get("/payments", response_model=list[PaymentResponse], summary="List all payments")
async def list_payments(
    status: PaymentStatus | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(_admin_only),
    service: PaymentService = Depends(get_payment_service),
) -> list[PaymentResponse]:
    payments = await service.list_all(status=status, limit=limit, offset=offset)
    return [PaymentResponse.model_validate(p) for p in payments]


@router.post(
    "/payments/{payment_id}/mark-paid",
    response_model=PaymentResponse,
    summary="Mark a payment as paid (cash/external tracking)",
    responses={422: {"description": "Payment is not PENDING"}},
)
async def mark_payment_paid(
    payment_id: uuid.UUID,
    payload: MarkPaidRequest,
    user: User = Depends(_admin_only),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    payment = await service.mark_paid(user.id, payment_id, payload.payment_method, payload.transaction_id)
    return PaymentResponse.model_validate(payment)


# --- Complaints (Section 29) ---


@router.get("/complaints", response_model=list[ComplaintResponse], summary="List all complaints")
async def list_complaints_admin(
    status: ComplaintStatus | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(_admin_only),
    service: ComplaintService = Depends(get_complaint_service),
) -> list[ComplaintResponse]:
    complaints = await service.list_all(status=status, limit=limit, offset=offset)
    return [ComplaintResponse.model_validate(c) for c in complaints]


@router.patch(
    "/complaints/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Update a complaint's status / add an admin response",
)
async def update_complaint_admin(
    complaint_id: uuid.UUID,
    payload: ComplaintAdminUpdate,
    user: User = Depends(_admin_only),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    complaint = await service.admin_update(user.id, complaint_id, payload)
    return ComplaintResponse.model_validate(complaint)


# --- Stats (Section 27) ---


@router.get("/stats", response_model=PlatformStatsResponse, summary="Platform-wide dashboard statistics")
async def get_stats(
    user: User = Depends(_admin_only),
    service: AdminStatsService = Depends(get_admin_stats_service),
) -> PlatformStatsResponse:
    return await service.get_stats()

