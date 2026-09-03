import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.nurse import Gender, PriceUnit, ShiftType
from app.models.user import User, UserRole
from app.schemas.nurse import (
    nurse_to_response,
    nurse_to_search_result,
    NurseCreateRequest,
    NurseDocumentResponse,
    NurseDocumentUploadRequest,
    NurseResponse,
    NurseSearchResult,
    NurseUpdateRequest,
)
from app.services.nurse_search_service import NurseSearchService
from app.services.nurse_service import NurseService

router = APIRouter(prefix="/nurses", tags=["Nurses"])


def get_nurse_service(db: AsyncSession = Depends(get_db)) -> NurseService:
    return NurseService(db)


def get_nurse_search_service(db: AsyncSession = Depends(get_db)) -> NurseSearchService:
    return NurseSearchService(db)


# NOTE: "/", "/me" and "/me/documents" routes are declared before
# "/{nurse_id}" so FastAPI matches the literal paths first — otherwise
# "me" (or the search route) would be parsed as a UUID nurse_id and 422
# instead of resolving correctly.


@router.get(
    "",
    response_model=list[NurseSearchResult],
    summary="Browse/search the nurse marketplace (Sections 14-15)",
    description=(
        "Public marketplace browse with server-side filters — gender, "
        "experience, specialty, rating, price range + payment frequency, "
        "shift availability, verification status, governorate. Filtering "
        "happens entirely at the database level, never client-side."
    ),
)
async def search_nurses(
    gender: Gender | None = None,
    min_experience_years: int | None = Query(default=None, ge=0),
    specialty_id: uuid.UUID | None = None,
    min_rating: float | None = Query(default=None, ge=0, le=5),
    price_min: float | None = Query(default=None, ge=0),
    price_max: float | None = Query(default=None, ge=0),
    payment_frequency: PriceUnit | None = None,
    shift_type: ShiftType | None = None,
    verified_only: bool = False,
    governorate: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE, UserRole.ADMIN)),
    service: NurseSearchService = Depends(get_nurse_search_service),
) -> list[NurseSearchResult]:
    nurses = await service.search(
        gender=gender,
        min_experience_years=min_experience_years,
        specialty_id=specialty_id,
        min_rating=min_rating,
        price_min=price_min,
        price_max=price_max,
        payment_frequency=payment_frequency,
        shift_type=shift_type,
        verified_only=verified_only,
        governorate=governorate,
        limit=limit,
        offset=offset,
    )
    return [nurse_to_search_result(n) for n in nurses]


@router.post(
    "/me",
    response_model=NurseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nurse onboarding — create professional profile",
    description=(
        "NURSE role only. Creates the professional profile with specialties, "
        "priced services, and availability. The nurse is NOT immediately "
        "active — is_approved stays false until an administrator verifies "
        "the uploaded documents (Phase 8)."
    ),
    responses={409: {"description": "Profile already exists"}, 422: {"description": "Unknown specialty/service id"}},
)
async def create_my_nurse_profile(
    payload: NurseCreateRequest,
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: NurseService = Depends(get_nurse_service),
) -> NurseResponse:
    nurse = await service.create_profile(user.id, payload)
    return nurse_to_response(nurse)


@router.get(
    "/me",
    response_model=NurseResponse,
    summary="Get the current nurse's own profile",
    responses={404: {"description": "No nurse profile yet"}},
)
async def get_my_nurse_profile(
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: NurseService = Depends(get_nurse_service),
) -> NurseResponse:
    nurse = await service.get_my_profile(user.id)
    return nurse_to_response(nurse)


@router.patch(
    "/me",
    response_model=NurseResponse,
    summary="Update the current nurse's profile",
    responses={404: {"description": "No nurse profile yet"}},
)
async def update_my_nurse_profile(
    payload: NurseUpdateRequest,
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: NurseService = Depends(get_nurse_service),
) -> NurseResponse:
    nurse = await service.update_profile(user.id, payload)
    return nurse_to_response(nurse)


@router.post(
    "/me/documents",
    response_model=NurseDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an uploaded verification document",
    description=(
        "Registers metadata for a document already uploaded to secure object "
        "storage. Status starts PENDING until an admin reviews it (Phase 8)."
    ),
)
async def upload_nurse_document(
    payload: NurseDocumentUploadRequest,
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: NurseService = Depends(get_nurse_service),
) -> NurseDocumentResponse:
    doc = await service.upload_document(user.id, payload)
    return NurseDocumentResponse.model_validate(doc)


@router.get(
    "/me/documents",
    response_model=list[NurseDocumentResponse],
    summary="List the current nurse's uploaded documents and their review status",
)
async def list_my_nurse_documents(
    user: User = Depends(require_roles(UserRole.NURSE)),
    service: NurseService = Depends(get_nurse_service),
) -> list[NurseDocumentResponse]:
    docs = await service.list_my_documents(user.id)
    return [NurseDocumentResponse.model_validate(d) for d in docs]


@router.get(
    "/{nurse_id}",
    response_model=NurseResponse,
    summary="Get a nurse's public profile",
    description="Publicly viewable by any authenticated user (patients browsing the marketplace).",
    responses={404: {"description": "Nurse not found"}},
)
async def get_nurse_public_profile(
    nurse_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE, UserRole.ADMIN)),
    service: NurseService = Depends(get_nurse_service),
) -> NurseResponse:
    nurse = await service.get_public_profile(nurse_id)
    return nurse_to_response(nurse)
