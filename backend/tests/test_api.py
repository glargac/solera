import uuid

from app.services.ical_sync import parse_ical
from tests.conftest import token_for

ICS = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:abc-1
SUMMARY:Reserved
DTSTART;VALUE=DATE:20261101
DTEND;VALUE=DATE:20261105
END:VEVENT
END:VCALENDAR
"""


def test_parse_ical():
    ev = parse_ical(ICS)
    assert len(ev) == 1 and ev[0]["uid"] == "abc-1"
    assert str(ev[0]["check_out"]) == "2026-11-05"


async def test_isolation_and_cleaning_task(client):
    a, b = uuid.uuid4(), uuid.uuid4()
    ha, hb = token_for(a), token_for(b, "b@test.com")
    r = await client.post("/api/v1/properties", json={"name": "Casa A"}, headers=ha)
    pid = r.json()["id"]
    assert (await client.get("/api/v1/properties", headers=hb)).json() == []
    r = await client.post("/api/v1/bookings", headers=ha, json={
        "property_id": pid, "check_in": "2026-11-01", "check_out": "2026-11-05"})
    assert r.status_code == 201
    token = r.json()["guide_token"]
    # Otro anfitrión no puede reservar en propiedad ajena
    r = await client.post("/api/v1/bookings", headers=hb, json={
        "property_id": pid, "check_in": "2026-12-01", "check_out": "2026-12-05"})
    assert r.status_code == 404
    tasks = await client.get("/api/v1/cleaning/tasks?date=2026-11-05", headers=ha)
    assert len(tasks.json()) == 1
    assert (await client.get("/api/v1/cleaning/tasks?date=2026-11-05", headers=hb)).json() == []
    # Completar sin 3 fotos falla
    tid = tasks.json()[0]["id"]
    assert (await client.post(f"/api/v1/cleaning/tasks/{tid}/complete", headers=ha)).status_code == 422
    # Guía pública
    g = await client.get(f"/api/v1/guests/guide/{token}")
    assert g.status_code == 200 and g.json()["property_name"] == "Casa A"


async def test_requires_auth(client):
    assert (await client.get("/api/v1/properties")).status_code in (401, 403)


async def test_rejects_unknown_kid_and_hs256(client):
    from jose import jwt as j
    bad_kid = token_for(uuid.uuid4(), kid="other")
    assert (await client.get("/api/v1/auth/me", headers=bad_kid)).status_code == 401
    hs = j.encode({"sub": str(uuid.uuid4()), "aud": "authenticated"}, "x", algorithm="HS256", headers={"kid": "test-key"})
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {hs}"})
    assert r.status_code == 401
