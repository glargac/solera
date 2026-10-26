from fastapi import APIRouter

from app.api.v1.endpoints import auth, bookings, cleaning, guests, properties

api_router = APIRouter()
for module in (auth, properties, bookings, cleaning, guests):
    api_router.include_router(module.router)
