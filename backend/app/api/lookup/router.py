from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.lookup_repository import LookupRepository
from app.schemas.lookup import ServiceResponse, SpecialtyResponse

router = APIRouter(tags=["Lookup"])


@router.get(
    "/specialties",
    response_model=list[SpecialtyResponse],
    summary="List active specialties",
    description="Configurable from the admin dashboard (Phase 8) — never hard-coded on the client.",
)
async def list_specialties(db: AsyncSession = Depends(get_db)) -> list[SpecialtyResponse]:
    items = await LookupRepository(db).list_specialties(active_only=True)
    return [SpecialtyResponse.model_validate(i) for i in items]


@router.get(
    "/services",
    response_model=list[ServiceResponse],
    summary="List active services",
    description="Configurable from the admin dashboard (Phase 8) — never hard-coded on the client.",
)
async def list_services(db: AsyncSession = Depends(get_db)) -> list[ServiceResponse]:
    items = await LookupRepository(db).list_services(active_only=True)
    return [ServiceResponse.model_validate(i) for i in items]
