"""
Security primitives: password hashing and JWT access/refresh tokens.

Design notes (Section 7 / 32 of spec):
- Passwords are never stored or logged in plaintext, only bcrypt hashes.
- Access tokens are short-lived; refresh tokens are longer-lived and carry a
  distinct `type` claim + are signed with a *different* secret, so an access
  token can never be replayed as a refresh token even if leaked.
- `jti` (token id) is included on refresh tokens to support future
  refresh-token rotation / revocation via Redis blacklist.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(
    subject: str,
    role: str,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    secret = settings.JWT_SECRET if token_type == "access" else settings.JWT_REFRESH_SECRET
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(
        subject=user_id,
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str, role: str) -> str:
    return _create_token(
        subject=user_id,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, token_type: TokenType) -> dict[str, Any]:
    """
    Decode & validate a token. Raises jose.JWTError on any failure
    (expired, bad signature, malformed).
    """
    secret = settings.JWT_SECRET if token_type == "access" else settings.JWT_REFRESH_SECRET
    payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != token_type:
        raise JWTError("Invalid token type")
    return payload
