"""
Repository layer: isolates raw DB queries from business logic (services/).
Keeping this thin and explicit makes it easy to unit test and to later swap
storage details without touching service/business logic.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self.db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password_hash: str,
        role: UserRole,
        phone: str | None = None,
        username: str | None = None,
    ) -> User:
        user = User(email=email, password_hash=password_hash, role=role, phone=phone, username=username)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_password(self, user: User, password_hash: str) -> User:
        user.password_hash = password_hash
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def list_all(
        self, role: UserRole | None = None, limit: int = 20, offset: int = 0
    ) -> list[User]:
        stmt = select(User)
        if role is not None:
            stmt = stmt.where(User.role == role)
        stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def set_active(self, user: User, is_active: bool) -> None:
        user.is_active = is_active
        await self.db.flush()
