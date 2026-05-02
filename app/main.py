from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import router as api_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.features.rbac.service import RBACSeeder

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with SessionLocal() as db:
        await RBACSeeder(db).seed_defaults()
    yield


app = FastAPI(title=settings.project_name, version="0.1.0", lifespan=lifespan)
app.include_router(api_router)

Instrumentator().instrument(app).expose(app)
