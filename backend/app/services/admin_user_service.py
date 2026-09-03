"""User management (Section 26): list, activate, deactivate accounts."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User, UserRole
from app.repositories.admin_action_repository import AdminActionRepository
from app.repositories.user_repository import UserRepository


class AdminUserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.audit = AdminActionRepository(db)

    async def list_users(
        self, role: UserRole | None = None, limit: int = 20, offset: int = 0
    ) -> list[User]:
        return await self.users.list_all(role=role, limit=limit, offset=offset)

    async def deactivate(self, admin_id: uuid.UUID, user_id: uuid.UUID, reason: str | None) -> User:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        await self.users.set_active(user, False)
        await self.audit.record(
            admin_id=admin_id,
            action_type="DEACTIVATE_USER",
            target_type="user",
            target_id=user.id,
            reason=reason,
        )
        await self.db.commit()
        return user

    async def activate(self, admin_id: uuid.UUID, user_id: uuid.UUID) -> User:
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        await self.users.set_active(user, True)
        await self.audit.record(
            admin_id=admin_id, action_type="ACTIVATE_USER", target_type="user", target_id=user.id
        )
        await self.db.commit()
        return user
