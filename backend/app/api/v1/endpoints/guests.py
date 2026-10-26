from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models import Booking, Property

router = APIRouter(prefix="/guests", tags=["guests"])


@router.get("/guide/{token}")
async def guide(token: str, session: AsyncSession = Depends(get_session)):
    """Guía pública del huésped, accesible por token de reserva (sin login)."""
    booking = (await session.exec(select(Booking).where(Booking.guide_token == token))).first()
    if booking is None:
        raise HTTPException(404, "Guía no encontrada")
    prop = await session.get(Property, booking.property_id)
    return {
        "property_name": prop.name,
        "city": prop.city,
        "address": prop.address,
        "guest_name": booking.guest_name,
        "check_in": booking.check_in,
        "check_out": booking.check_out,
        "wifi_name": prop.wifi_name,
        "wifi_password": prop.wifi_password,
        "checkin_instructions": prop.checkin_instructions,
        "house_rules": prop.house_rules,
        "emergency_contacts": prop.emergency_contacts,
    }
