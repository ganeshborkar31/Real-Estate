from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.properties import amenities_router
from app.api.v1.endpoints.properties import documents_router
from app.api.v1.endpoints.properties import images_router as property_images_router
from app.api.v1.endpoints.properties import router as properties_router
from app.api.v1.endpoints.rbac import router as rbac_router
from app.api.v1.endpoints.users import router as users_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(rbac_router)
router.include_router(properties_router)
router.include_router(property_images_router)
router.include_router(amenities_router)
router.include_router(documents_router)
