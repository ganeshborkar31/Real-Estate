from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router


router = APIRouter()
router.include_router(health_router, prefix="/api/v1/health", tags=["Health"])
router.include_router(v1_router, prefix="/api/v1")
