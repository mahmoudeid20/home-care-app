from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis_dep
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    SendOTPRequest,
    VerifyOTPRequest,
    ValidateNationalIDRequest,
    NationalIDResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_dep),
) -> AuthService:
    return AuthService(db=db, redis=redis)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient or nurse account",
    description=(
        "Creates a new user account with role PATIENT or NURSE. ADMIN accounts "
        "cannot be created through this endpoint. Returns the created user and "
        "a token pair. Passwords are hashed with bcrypt before storage."
    ),
    responses={
        409: {"description": "Email or phone already registered"},
        422: {"description": "Validation error (weak password, invalid email, etc.)"},
    },
)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    return await service.register(
        email=payload.email,
        password=payload.password,
        role=payload.role,
        phone=payload.phone,
        username=payload.username,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
    responses={401: {"description": "Invalid credentials or inactive account"}},
)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    return await service.login(email=payload.email, password=payload.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new access/refresh token pair",
    description="Refresh tokens are rotated: the old token is invalidated once used.",
    responses={401: {"description": "Invalid, expired, or revoked refresh token"}},
)
async def refresh(
    payload: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate a refresh token",
)
async def logout(
    payload: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout(payload.refresh_token)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Request a password reset token",
    description=(
        "Always returns 204 whether or not the email exists, to prevent user "
        "enumeration. If the account exists, a reset token is generated "
        "(delivery via email/SMS/OTP is a future integration point)."
    ),
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.forgot_password(payload.email)


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset password using a valid reset token",
    responses={422: {"description": "Invalid or expired reset token"}},
)
async def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.reset_password(payload.token, payload.new_password)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
    responses={401: {"description": "Not authenticated"}},
)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post(
    "/send-otp",
    summary="Generate and send a 6-digit OTP code via Email or SMS",
    status_code=status.HTTP_200_OK,
)
async def send_otp(
    payload: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.otp_service import OTPService
    from app.models.otp import OTPChannel, OTPPurpose

    channel = OTPChannel.SMS if payload.channel.upper() == "SMS" else OTPChannel.EMAIL
    purpose = OTPPurpose(payload.purpose.upper()) if payload.purpose.upper() in OTPPurpose.__members__ else OTPPurpose.REGISTRATION

    service = OTPService(db)
    code = await service.generate_otp(recipient=payload.recipient, channel=channel, purpose=purpose)
    return {
        "message": "تم إرسال رمز التحقق بنجاح",
        "channel": channel.value,
        "expires_in_minutes": 10,
        "debug_code": code if settings.ENV == "development" else None,
    }


@router.post(
    "/verify-otp",
    summary="Verify a 6-digit OTP code",
    status_code=status.HTTP_200_OK,
)
async def verify_otp(
    payload: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.otp_service import OTPService
    from app.models.otp import OTPPurpose

    purpose = OTPPurpose(payload.purpose.upper()) if payload.purpose.upper() in OTPPurpose.__members__ else OTPPurpose.REGISTRATION
    service = OTPService(db)
    verified = await service.verify_otp(recipient=payload.recipient, code=payload.code, purpose=purpose)
    return {
        "verified": verified,
        "message": "تم التحقق بنجاح",
    }


@router.post(
    "/validate-national-id",
    response_model=NationalIDResponse,
    summary="Validate and extract birthdate, governorate, and gender from Egyptian National ID",
)
async def validate_national_id(payload: ValidateNationalIDRequest) -> NationalIDResponse:
    from app.utils.egyptian_id import parse_egyptian_national_id
    info = parse_egyptian_national_id(payload.national_id)
    return NationalIDResponse(**info.to_dict())


@router.post(
    "/accept-terms",
    summary="Record user acceptance of terms of service and privacy policy",
    status_code=status.HTTP_200_OK,
)
async def accept_terms(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from datetime import datetime, timezone
    # Update user acceptance timestamp if field exists
    if hasattr(user, "terms_accepted_at"):
        user.terms_accepted_at = datetime.now(timezone.utc)
        await db.commit()
    return {"accepted": True, "message": "تمت الموافقة على الشروط والخصوصية بنجاح"}

