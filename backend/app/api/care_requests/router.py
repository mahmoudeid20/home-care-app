import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_llm_client_dep, require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.ai_extraction import AIExtractionRequest, AIExtractionResult
from app.schemas.care_request import (
    CareRequestCreate,
    CareRequestResponse,
    CareRequestUpdate,
    care_request_to_response,
)
from app.schemas.matching import NurseMatchResult
from app.services.ai_extraction_service import AIExtractionService
from app.services.care_request_service import CareRequestService
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/care-requests", tags=["Care Requests"])


def get_care_request_service(db: AsyncSession = Depends(get_db)) -> CareRequestService:
    return CareRequestService(db)


def get_matching_service(db: AsyncSession = Depends(get_db)) -> MatchingService:
    return MatchingService(db)


def get_ai_extraction_service(
    db: AsyncSession = Depends(get_db), llm_client=Depends(get_llm_client_dep)
) -> AIExtractionService:
    return AIExtractionService(db, llm_client=llm_client)


@router.post(
    "/extract",
    response_model=AIExtractionResult,
    summary="AI-extract structured requirements from free text (Section 22)",
    description=(
        "PATIENT role only. Extracts scheduling/demographic/care-type fields from "
        "a free-text description to pre-fill the care request form — this endpoint "
        "never creates a care request itself, and the extraction never diagnoses "
        "or comments on the medical content (Section 2's healthcare-safety "
        "boundary). Review and submit the final values via POST /care-requests "
        "as normal."
    ),
    responses={
        422: {"description": "AI extraction is not configured on this server (no LLM_API_KEY set)"},
    },
)
async def extract_requirements(
    payload: AIExtractionRequest,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: AIExtractionService = Depends(get_ai_extraction_service),
) -> AIExtractionResult:
    return await service.extract(payload.text)


@router.post(
    "",
    response_model=CareRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a care request",
    description=(
        "PATIENT role only. Submits the full multi-step request in one call "
        "(the mobile app splits this into 6 steps client-side — Sections 9-13: "
        "patient info, required care, nurse requirements, location, schedule, "
        "budget). This endpoint never diagnoses or interprets the medical "
        "condition text — it is stored as-is for nurses/admins to read."
    ),
    responses={
        404: {"description": "No patient profile yet — create one first"},
        422: {"description": "Unknown service/specialty id or validation error"},
    },
)
async def create_care_request(
    payload: CareRequestCreate,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: CareRequestService = Depends(get_care_request_service),
) -> CareRequestResponse:
    cr = await service.create(user.id, payload)
    return care_request_to_response(cr)


@router.get(
    "",
    response_model=list[CareRequestResponse],
    summary="List the current patient's own care requests",
)
async def list_my_care_requests(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: CareRequestService = Depends(get_care_request_service),
) -> list[CareRequestResponse]:
    items = await service.list_mine(user.id, limit=limit, offset=offset)
    return [care_request_to_response(cr) for cr in items]


@router.get(
    "/{care_request_id}",
    response_model=CareRequestResponse,
    summary="Get a care request (owning patient, or a nurse who applied to it)",
    responses={
        403: {"description": "Not your care request and you have no application for it"},
        404: {"description": "Care request not found"},
    },
)
async def get_care_request(
    care_request_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: CareRequestService = Depends(get_care_request_service),
) -> CareRequestResponse:
    cr = await service.get(user.id, care_request_id)
    return care_request_to_response(cr)


@router.get(
    "/{care_request_id}/matches",
    response_model=list[NurseMatchResult],
    summary="Get ranked nurse recommendations for a care request (Section 21)",
    description=(
        "Rule-based matching engine: skills 30%, experience 20%, "
        "location/distance 15%, availability 15%, price 10%, rating 5%, "
        "verification 5% (weights are admin-configurable, not hard-coded — "
        "see /admin/matching-weights). Hard filters: nurse must be approved "
        "and not suspended; if verified_nurses_only is set, only fully "
        "verified nurses are returned; if preferred_nurse_gender is set, "
        "only matching-gender nurses are returned."
    ),
    responses={
        403: {"description": "Not your care request"},
        404: {"description": "Care request not found"},
    },
)
async def get_care_request_matches(
    care_request_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: MatchingService = Depends(get_matching_service),
) -> list[NurseMatchResult]:
    return await service.get_matches(user.id, care_request_id, limit=limit)


@router.patch(
    "/{care_request_id}",
    response_model=CareRequestResponse,
    summary="Update a care request (owner only, OPEN status only)",
    responses={
        403: {"description": "Not your care request"},
        404: {"description": "Care request not found"},
        422: {"description": "Not editable in the current status, or invalid field"},
    },
)
async def update_care_request(
    care_request_id: uuid.UUID,
    payload: CareRequestUpdate,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: CareRequestService = Depends(get_care_request_service),
) -> CareRequestResponse:
    cr = await service.update(user.id, care_request_id, payload)
    return care_request_to_response(cr)


@router.post(
    "/{care_request_id}/cancel",
    response_model=CareRequestResponse,
    summary="Cancel a care request (owner only)",
    responses={
        403: {"description": "Not your care request"},
        404: {"description": "Care request not found"},
        422: {"description": "Cannot be cancelled in the current status"},
    },
)
async def cancel_care_request(
    care_request_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: CareRequestService = Depends(get_care_request_service),
) -> CareRequestResponse:
    cr = await service.cancel(user.id, care_request_id)
    return care_request_to_response(cr)
