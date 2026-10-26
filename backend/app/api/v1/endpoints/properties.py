import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select

from app.core.database import get_session
from app.core.security import require_role
from app.models import Property, Role, User
from app.services.ical_sync import sync_property

router = APIRouter(prefix="/properties", tags=["properties"])
host_only = require_role(Role.host)


class PropertyIn(SQLModel):
    name: str
    city: str = "Málaga"
    address: str = ""
    nightly_price: float = 100.0
    cleaning_fee: float = 0.0
    ical_url: str | None = None
    wifi_name: str = ""
    wifi_password: str = ""
    checkin_instructions: str = ""
    house_rules: str = ""
    emergency_contacts: dict = {}


async def _own(session: AsyncSession, pid: uuid.UUID, user: User) -> Property:
    prop = await session.get(Property, pid)
    if prop is None or prop.owner_id != user.id:
        raise HTTPException(404, "Propiedad no encontrada")
    return prop


@router.get("", response_model=list[Property])
async def list_properties(user: User = Depends(host_only), session: AsyncSession = Depends(get_session)):
    return (await session.exec(select(Property).where(Property.owner_id == user.id))).all()


@router.post("", response_model=Property, status_code=201)
async def create_property(data: PropertyIn, user: User = Depends(host_only), session: AsyncSession = Depends(get_session)):
    prop = Property(**data.model_dump(), owner_id=user.id)
    session.add(prop)
    await session.commit()
    await session.refresh(prop)
    return prop


@router.put("/{pid}", response_model=Property)
async def update_property(pid: uuid.UUID, data: PropertyIn, user: User = Depends(host_only), session: AsyncSession = Depends(get_session)):
    prop = await _own(session, pid, user)
    for k, v in data.model_dump().items():
        setattr(prop, k, v)
    session.add(prop)
    await session.commit()
    await session.refresh(prop)
    return prop


@router.delete("/{pid}", status_code=204)
async def delete_property(pid: uuid.UUID, user: User = Depends(host_only), session: AsyncSession = Depends(get_session)):
    await session.delete(await _own(session, pid, user))
    await session.commit()


@router.post("/{pid}/sync")
async def sync_now(pid: uuid.UUID, user: User = Depends(host_only), session: AsyncSession = Depends(get_session)):
    prop = await _own(session, pid, user)
    if not prop.ical_url:
        raise HTTPException(400, "La propiedad no tiene URL iCal")
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(prop.ical_url)
        resp.raise_for_status()
    return {"synced": await sync_property(session, prop, resp.content)}
