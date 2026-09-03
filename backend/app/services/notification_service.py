"""
Central place other services call to notify a user (Section 25's trigger
list). Every notification is persisted first, so the in-app notification
center always has the full history even if push delivery fails or the
device is offline, then a push is attempted through FCMClient.

Callers (ApplicationService, BookingService, ChatService, ReviewService,
and eventually the admin document-verification flow in Phase 8) commit
their own transaction; NotificationRepository.create only flushes, so it
participates in the caller's existing transaction rather than opening a
separate one.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.notification import Notification, NotificationType
from app.repositories.notification_repository import NotificationRepository
from app.services.fcm_client import fcm_client


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notifications = NotificationRepository(db)

    async def notify(
        self,
        user_id: uuid.UUID,
        type_: NotificationType,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> Notification:
        notification = await self.notifications.create(user_id, type_, title, body, data)
        await fcm_client.send(user_id, title, body, data)
        return notification

    async def list_mine(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[Notification]:
        return await self.notifications.list_for_user(user_id, limit=limit, offset=offset)

    async def unread_count(self, user_id: uuid.UUID) -> int:
        return await self.notifications.count_unread(user_id)

    async def mark_read(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> Notification:
        notification = await self.notifications.get_by_id(notification_id)
        if not notification:
            raise NotFoundError("Notification not found")
        if notification.user_id != user_id:
            raise ForbiddenError("Not your notification")
        await self.notifications.mark_read(notification)
        await self.db.commit()
        return notification
