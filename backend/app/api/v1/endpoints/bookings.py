import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select

from app.core.database import get_session
from app.core.security import require_role
from app.models import Booking, BookingSource, Property, Role, User
from app.services.cleaning_tasks import ensure_cleaning_task

router = APIRouter(prefix="/bookings", tags=["bookings"])
host_only = require_role(Role.host)


class BookingIn(SQLModel):
    property_id: uuid.UUID
    guest_name: str = ""
    check_in: dt.date
    check_out: dt.date
    total_price: float = 0.0
    source: BookingSource = BookingSource.manual


async def _check_owner(session: AsyncSession, property_id: uuid.UUID, user: User) -> None:
    prop = await session.get(Property, property_id)
    if prop is None or prop.owner_id != user.id:
        raise HTTPException(404, "Propiedad no encontrada")


@router.get("", response_model=list[Booking])
async def list_bookings(
    property_id: uuid.UUID | None = None,
    user: User = Depends(host_only),
    session: AsyncSession = Depends(get_session),
):
    q = select(Booking).join(Property).where(Property.owner_id == user.id)
    if property_id:
        q = q.where(Booking.property_id == property_id)
    return (await session.exec(q.order_by(Booking.check_in))).all()


@router.post("", response_model=Booking, status_code=201)
async def create_booking(data: BookingIn, user: User = Depends(host_only), session: AsyncSession = Depends(get_session)):
    if data.check_out <= data.check_in:
        raise HTTPException(422, "check_out debe ser posterior a check_in")
    await _check_owner(session, data.property_id, user)
    booking = Booking(**data.model_dump())
    session.add(booking)
    await session.flush()
    await ensure_cleaning_task(session, booking)
    await session.commit()
    await session.refresh(booking)
    return booking


@router.delete("/{bid}", status_code=204)
async def delete_booking(bid: uuid.UUID, user: User = Depends(host_only), session: AsyncSession = Depends(get_session)):
    booking = await session.get(Booking, bid)
    if booking is None:
        raise HTTPException(404, "Reserva no encontrada")
    await _check_owner(session, booking.property_id, user)
    await session.delete(booking)
    await session.commit()
