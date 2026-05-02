from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis
from app.core.security import get_current_user
from app.db.session import get_db
from app.features.auth.service import AuthService
from app.features.users.schemas import (
    EmailVerificationRequest,
    EmailVerificationSendRequest,
    OTPVerifyRequest,
    OTPSendRequest,
    TokenRefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["AUTH"])


@router.post("/send-otp")
async def send_otp(
    request: OTPSendRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> dict:
    return await AuthService(db, redis_client).send_otp(request.mobile_number)


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> TokenResponse:
    result = await AuthService(db, redis_client).verify_otp(
        mobile_number=request.mobile_number,
        otp=request.otp,
        full_name=request.full_name,
    )
    return TokenResponse(**result)


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> TokenResponse:
    result = await AuthService(db, redis_client).refresh_access_token(request.refresh_token)
    return TokenResponse(**result)


@router.post("/send-email-verification")
async def send_email_verification(
    request: EmailVerificationSendRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> dict:
    return await AuthService(db, redis_client).send_email_verification(
        user_id=current_user["user_id"],
        email=request.email,
    )


@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> dict:
    await AuthService(db, redis_client).verify_email(request.token)
    return {"message": "Email verified successfully"}
