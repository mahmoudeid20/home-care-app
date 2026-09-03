import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.review import ReviewCreate, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(tags=["Reviews"])


def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    return ReviewService(db)


@router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Review a nurse after a completed booking (Section 24)",
    description=(
        "PATIENT role only, owner of the booking only. Only allowed once "
        "the booking is COMPLETED; transitions it to REVIEWED. One review "
        "per booking — a second attempt returns 409."
    ),
    responses={
        403: {"description": "Not your booking"},
        404: {"description": "Booking not found, or no patient profile yet"},
        409: {"description": "This booking has already been reviewed"},
        422: {"description": "Booking is not COMPLETED yet"},
    },
)
async def create_review(
    payload: ReviewCreate,
    user: User = Depends(require_roles(UserRole.PATIENT)),
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    review = await service.create(user.id, payload)
    return ReviewResponse.model_validate(review)


@router.get(
    "/nurses/{nurse_id}/reviews",
    response_model=list[ReviewResponse],
    summary="List a nurse's reviews (public - Section 16 profile 'Reviews' section)",
)
async def list_nurse_reviews(
    nurse_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE, UserRole.ADMIN)),
    service: ReviewService = Depends(get_review_service),
) -> list[ReviewResponse]:
    reviews = await service.list_for_nurse(nurse_id, limit=limit, offset=offset)
    return [ReviewResponse.model_validate(r) for r in reviews]
