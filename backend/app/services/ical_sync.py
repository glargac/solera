import datetime as dt
import logging

import httpx
from icalendar import Calendar
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.database import async_session
from app.models import Booking, BookingSource, Property
from app.services.cleaning_tasks import ensure_cleaning_task

log = logging.getLogger(__name__)


def _as_date(value) -> dt.date:
    return value.date() if isinstance(value, dt.datetime) else value


def parse_ical(text: str | bytes) -> list[dict]:
    """Devuelve eventos como dicts {uid, summary, check_in, check_out}."""
    cal = Calendar.from_ical(text)
    events = []
    for comp in cal.walk("VEVENT"):
        if "DTSTART" not in comp or "DTEND" not in comp:
            continue
        events.append(
            {
                "uid": str(comp.get("UID")),
                "summary": str(comp.get("SUMMARY", "")),
                "check_in": _as_date(comp.decoded("DTSTART")),
                "check_out": _as_date(comp.decoded("DTEND")),
            }
        )
    return events


async def sync_property(session: AsyncSession, prop: Property, text: str | bytes) -> int:
    """Upsert por UID. Devuelve el número de eventos procesados."""
    events = parse_ical(text)
    for ev in events:
        res = await session.exec(
            select(Booking).where(
                Booking.property_id == prop.id, Booking.external_uid == ev["uid"]
            )
        )
        booking = res.first()
        if booking is None:
            booking = Booking(
                property_id=prop.id,
                source=BookingSource.ical,
                external_uid=ev["uid"],
                guest_name=ev["summary"],
                check_in=ev["check_in"],
                check_out=ev["check_out"],
            )
        else:
            booking.check_in, booking.check_out = ev["check_in"], ev["check_out"]
        session.add(booking)
        await session.flush()
        await ensure_cleaning_task(session, booking)
    await session.commit()
    return len(events)


async def sync_all() -> None:
    async with async_session() as session:
        props = (await session.exec(select(Property).where(Property.ical_url.is_not(None)))).all()
        for prop in props:
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    resp = await client.get(prop.ical_url)
                    resp.raise_for_status()
                await sync_property(session, prop, resp.content)
            except Exception:
                log.exception("Fallo sincronizando iCal de %s", prop.id)
