"""
Request/response schemas for authentication endpoints.

Never include password_hash or any raw secret in a response schema
(Section 7 / 32: "Never expose passwords or sensitive authentication data").
"""
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str | None = Field(default=None, min_length=3, max_length=50)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    password: str = Field(min_length=8, max_length=72)
    role: UserRole = Field(
        description="PATIENT or NURSE. ADMIN accounts are created by existing admins only."
    )

    @field_validator("role")
    @classmethod
    def role_must_be_self_registerable(cls, v: UserRole) -> UserRole:
        if v == UserRole.ADMIN:
            raise ValueError("ADMIN accounts cannot self-register")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 bytes")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str | None = None
    phone: str | None
    role: UserRole
    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class SendOTPRequest(BaseModel):
    recipient: str
    channel: str = "EMAIL"  # EMAIL or SMS
    purpose: str = "REGISTRATION"


class VerifyOTPRequest(BaseModel):
    recipient: str
    code: str = Field(min_length=6, max_length=6)
    purpose: str = "REGISTRATION"


class ValidateNationalIDRequest(BaseModel):
    national_id: str


class NationalIDResponse(BaseModel):
    national_id: str
    is_valid: bool
    birth_date: str | None = None
    governorate: str | None = None
    gender: str | None = None
    error_message: str | None = None

