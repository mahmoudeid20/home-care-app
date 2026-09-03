from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreateRequest, PatientResponse, PatientUpdateRequest
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


def get_patient_service(db: AsyncSession = Depends(get_db)) -> PatientService:
    return PatientService(db)


@router.post(
    "/me",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create the current user's patient profile",
    description="PATIENT role only. One profile per account (409 if one already exists).",
    responses={409: {"description": "Profile already exists"}},
)
async def create_my_patient_profile(
    payload: PatientCreateRequest,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    patient = await service.create_profile(user.id, payload)
    return PatientResponse.model_validate(patient)


@router.get(
    "/me",
    response_model=PatientResponse,
    summary="Get the current user's patient profile",
    responses={404: {"description": "No patient profile yet"}},
)
async def get_my_patient_profile(
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    patient = await service.get_my_profile(user.id)
    return PatientResponse.model_validate(patient)


@router.patch(
    "/me",
    response_model=PatientResponse,
    summary="Update the current user's patient profile",
    responses={404: {"description": "No patient profile yet"}},
)
async def update_my_patient_profile(
    payload: PatientUpdateRequest,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    patient = await service.update_profile(user.id, payload)
    return PatientResponse.model_validate(patient)
