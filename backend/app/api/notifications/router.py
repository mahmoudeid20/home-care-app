import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="List the current user's notifications (in-app notification center)",
)
async def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE, UserRole.ADMIN)),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationResponse]:
    items = await service.list_mine(user.id, limit=limit, offset=offset)
    return [NotificationResponse.model_validate(n) for n in items]


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get the count of unread notifications (for a badge icon)",
)
async def unread_count(
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE, UserRole.ADMIN)),
    service: NotificationService = Depends(get_notification_service),
) -> UnreadCountResponse:
    count = await service.unread_count(user.id)
    return UnreadCountResponse(unread_count=count)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a notification as read",
    responses={
        403: {"description": "Not your notification"},
        404: {"description": "Notification not found"},
    },
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    user: User = Depends(require_roles(UserRole.PATIENT, UserRole.NURSE, UserRole.ADMIN)),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    notification = await service.mark_read(user.id, notification_id)
    return NotificationResponse.model_validate(notification)
