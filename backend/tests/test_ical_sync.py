import uuid

import pytest
from sqlmodel import select

from app.core import database
from app.models import Booking, CleaningTask, Property
from app.services.ical_sync import parse_ical, sync_property


def ics(uid="u1", start="20261101", end="20261105", summary="Reserved") -> bytes:
    return f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:{uid}
SUMMARY:{summary}
DTSTART;VALUE=DATE:{start}
DTEND;VALUE=DATE:{end}
END:VEVENT
END:VCALENDAR
""".encode()


@pytest.fixture
async def prop(client):
    async with database.async_session() as s:
        owner = uuid.uuid4()
        from app.models import User
        s.add(User(id=owner, email="o@test.com"))
        await s.commit()
        p = Property(owner_id=owner, name="Casa", ical_url="http://x/cal.ics")
        s.add(p)
        await s.commit()
        await s.refresh(p)
        return p


async def count(model):
    async with database.async_session() as s:
        return len((await s.exec(select(model))).all())


def test_datetime_events_become_dates():
    text = b"""BEGIN:VCALENDAR
BEGIN:VEVENT
UID:dt
DTSTART:20261101T150000Z
DTEND:20261105T110000Z
END:VEVENT
END:VCALENDAR
"""
    ev = parse_ical(text)[0]
    assert str(ev["check_in"]) == "2026-11-01" and str(ev["check_out"]) == "2026-11-05"


def test_events_without_dates_are_skipped():
    text = b"BEGIN:VCALENDAR\nBEGIN:VEVENT\nUID:x\nEND:VEVENT\nEND:VCALENDAR\n"
    assert parse_ical(text) == []


async def test_sync_is_idempotent(prop):
    async with database.async_session() as s:
        assert await sync_property(s, prop, ics()) == 1
    async with database.async_session() as s:
        await sync_property(s, prop, ics())
    assert await count(Booking) == 1
    assert await count(CleaningTask) == 1


async def test_changed_dates_update_booking_and_cleaning(prop):
    async with database.async_session() as s:
        await sync_property(s, prop, ics(end="20261105"))
    async with database.async_session() as s:
        await sync_property(s, prop, ics(end="20261107"))
    async with database.async_session() as s:
        b = (await s.exec(select(Booking))).one()
        t = (await s.exec(select(CleaningTask))).one()
    assert str(b.check_out) == "2026-11-07" and str(t.date) == "2026-11-07"


async def test_multiple_events(prop):
    def event(uid, start, end):
        return f"BEGIN:VEVENT\nUID:{uid}\nDTSTART;VALUE=DATE:{start}\nDTEND;VALUE=DATE:{end}\nEND:VEVENT\n"

    text = ("BEGIN:VCALENDAR\nVERSION:2.0\n" + event("a", "20261101", "20261105")
            + event("b", "20261201", "20261203") + "END:VCALENDAR\n").encode()
    async with database.async_session() as s:
        assert await sync_property(s, prop, text) == 2
    assert await count(Booking) == 2
    assert await count(CleaningTask) == 2


def test_malformed_ical_raises():
    with pytest.raises(Exception):
        parse_ical(b"esto no es un calendario")
