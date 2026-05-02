from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis
from app.core.security import require_permission
from app.db.session import get_db
from app.features.rbac.schemas import AssignPermissionRequest, AssignRoleRequest, RoleCreate, RoleOut
from app.features.rbac.service import PermissionService, RBACSeeder, RoleService, invalidate_user_access_cache
from app.features.users.schemas import UserOut
from app.features.users.service import UserService

router = APIRouter(tags=["RBAC"])


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    _: bool = Depends(require_permission("user:view")),
    db: AsyncSession = Depends(get_db),
) -> list[RoleOut]:
    roles = await RoleService(db).list_roles()
    return [RoleOut.model_validate(role) for role in roles]


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreate,
    _: bool = Depends(require_permission("user:manage")),
    db: AsyncSession = Depends(get_db),
) -> RoleOut:
    role = await RoleService(db).create_role(request.name, request.description)
    return RoleOut.model_validate(role)


@router.post("/roles/{role_id}/permissions", response_model=RoleOut)
async def add_permission_to_role(
    role_id: str,
    request: AssignPermissionRequest,
    _: bool = Depends(require_permission("user:manage")),
    db: AsyncSession = Depends(get_db),
) -> RoleOut:
    role = await RoleService(db).assign_permission(role_id, request.permission_id)
    return RoleOut.model_validate(role)


@router.post("/users/{user_id}/roles", response_model=UserOut)
async def add_role_to_user(
    user_id: str,
    request: AssignRoleRequest,
    _: bool = Depends(require_permission("user:manage")),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> UserOut:
    user_service = UserService(db)
    user = await user_service.add_role_to_user(user_id, request.role_id)
    await invalidate_user_access_cache(redis_client, user_id)
    return UserOut.model_validate(user)


@router.post("/rbac/seed-defaults")
async def seed_rbac_defaults(
    _: bool = Depends(require_permission("user:manage")),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await RBACSeeder(db).seed_defaults()
    return {"message": "Default roles and permissions seeded"}
