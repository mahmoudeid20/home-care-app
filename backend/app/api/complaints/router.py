import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.complaint import ComplaintCreate, ComplaintResponse
from app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/complaints", tags=["Complaints"])


def get_complaint_service(db: AsyncSession = Depends(get_db)) -> ComplaintService:
    return ComplaintService(db)


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="File a complaint (Section 29)",
    description="Either a patient or a nurse can file a complaint, optionally tied to a booking.",
)
async def create_complaint(
    payload: ComplaintCreate,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    complaint = await service.create(user.id, payload)
    return ComplaintResponse.model_validate(complaint)


@router.get("", response_model=list[ComplaintResponse], summary="List my own complaints")
async def list_my_complaints(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: ComplaintService = Depends(get_complaint_service),
) -> list[ComplaintResponse]:
    items = await service.list_mine(user.id, limit=limit, offset=offset)
    return [ComplaintResponse.model_validate(c) for c in items]


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get one of my own complaints",
    responses={403: {"description": "Not your complaint"}, 404: {"description": "Not found"}},
)
async def get_my_complaint(
    complaint_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE)),
    service: ComplaintService = Depends(get_complaint_service),
) -> ComplaintResponse:
    complaint = await service.get_own(user.id, complaint_id)
    return ComplaintResponse.model_validate(complaint)
