from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.core.security import require_permission
from app.db.session import get_db
from app.features.rera.schemas import VerifyKYCRequest
from app.features.rera.service import RERAService
from app.features.trust.service import TrustService
from app.features.users.schemas import UserOut, UserSelfUpdateRequest, UserWithAccessOut
from app.features.users.service import UserService

router = APIRouter(prefix="/users", tags=["USERS"])


@router.get("/me", response_model=UserWithAccessOut)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserWithAccessOut:
    service = UserService(db)
    user = await service.get_user(current_user["user_id"])
    return UserWithAccessOut(
        **UserOut.model_validate(user).model_dump(),
        roles=service.get_role_names(user),
        permissions=service.get_permission_names(user),
    )


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserSelfUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    service = UserService(db)
    user = await service.update_self(
        user_id=current_user["user_id"],
        full_name=payload.full_name,
        email=payload.email,
    )
    return UserOut.model_validate(user)


@router.get("/{user_id}")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = UserService(db)
    user = await service.get_user(user_id)
    badges = await TrustService(db).list_user_badges(user.id)
    return {
        "success": True,
        "data": {
            **UserOut.model_validate(user).model_dump(),
            "badges": [b.name for b in badges],
        },
        "message": "User profile fetched successfully",
    }


@router.post("/{user_id}/verify-kyc", response_model=UserOut)
async def verify_kyc(
    user_id: str,
    payload: VerifyKYCRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission("user:verify")),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await RERAService(db).verify_user_kyc(
        user_id=user_id,
        verifier_id=current_user["user_id"],
        kyc_type=payload.kyc_type.value,
        kyc_document_url=payload.kyc_document_url,
    )
    return UserOut.model_validate(user)
