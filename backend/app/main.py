from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.services.ical_sync import sync_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(sync_all, "interval", minutes=settings.ical_sync_minutes)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="SOLORA API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",  # puertos de desarrollo
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
