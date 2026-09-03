"""
Auth business logic. Endpoints (api/auth/router.py) should stay thin and
delegate everything here, so the logic is independently unit-testable.
"""
import uuid
from datetime import timedelta

from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, TokenResponse, UserResponse

REFRESH_BLACKLIST_PREFIX = "blacklist:refresh:"
PASSWORD_RESET_PREFIX = "pwreset:"


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
        self.users = UserRepository(db)

    def _issue_tokens(self, user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(str(user.id), user.role.value),
            refresh_token=create_refresh_token(str(user.id), user.role.value),
        )

    async def register(
        self,
        email: str,
        password: str,
        role: UserRole,
        phone: str | None = None,
        username: str | None = None,
    ) -> AuthResponse:
        if await self.users.get_by_email(email):
            raise ConflictError("An account with this email already exists")
        if username and await self.users.get_by_username(username):
            raise ConflictError("An account with this username already exists")
        if phone and await self.users.get_by_phone(phone):
            raise ConflictError("An account with this phone number already exists")

        user = await self.users.create(
            email=email,
            password_hash=hash_password(password),
            role=role,
            phone=phone,
            username=username,
        )
        await self.db.commit()

        tokens = self._issue_tokens(user)
        return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)

    async def login(self, email: str, password: str) -> AuthResponse:
        user = await self.users.get_by_email(email)
        # Constant-shape error regardless of whether the email exists, to avoid
        # user enumeration.
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated")

        tokens = self._issue_tokens(user)
        return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, token_type="refresh")
        except JWTError:
            raise UnauthorizedError("Invalid or expired refresh token")

        jti = payload.get("jti")
        if jti and await self.redis.get(f"{REFRESH_BLACKLIST_PREFIX}{jti}"):
            raise UnauthorizedError("Refresh token has been revoked")

        user = await self.users.get_by_id(uuid.UUID(payload["sub"]))
        if not user or not user.is_active:
            raise UnauthorizedError("Account not found or inactive")

        # Rotate: blacklist the old refresh token so it cannot be reused.
        if jti:
            ttl = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            await self.redis.set(f"{REFRESH_BLACKLIST_PREFIX}{jti}", "1", ex=ttl)

        return self._issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, token_type="refresh")
        except JWTError:
            # Already invalid/expired — logout is idempotent, nothing to do.
            return
        jti = payload.get("jti")
        if jti:
            ttl = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            await self.redis.set(f"{REFRESH_BLACKLIST_PREFIX}{jti}", "1", ex=ttl)

    async def forgot_password(self, email: str) -> None:
        """
        Always succeeds silently (no user enumeration). If the account
        exists, a reset token is generated and stored with a short TTL.
        Actual delivery (email/SMS/OTP) is a Phase-2+ integration point —
        for now we log it so the flow is testable end-to-end in dev.
        """
        user = await self.users.get_by_email(email)
        if not user:
            return
        reset_token = str(uuid.uuid4())
        await self.redis.set(f"{PASSWORD_RESET_PREFIX}{reset_token}", str(user.id), ex=900)
        # TODO(Phase 2+): send via email/SMS provider instead of logging.
        print(f"[DEV ONLY] Password reset token for {email}: {reset_token}")

    async def reset_password(self, token: str, new_password: str) -> None:
        user_id = await self.redis.get(f"{PASSWORD_RESET_PREFIX}{token}")
        if not user_id:
            raise ValidationAppError("Invalid or expired reset token")

        user = await self.users.get_by_id(uuid.UUID(user_id))
        if not user:
            raise ValidationAppError("Invalid or expired reset token")

        await self.users.update_password(user, hash_password(new_password))
        await self.db.commit()
        await self.redis.delete(f"{PASSWORD_RESET_PREFIX}{token}")
