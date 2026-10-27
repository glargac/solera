import uuid

from tests.conftest import token_for
from tests.helpers import make_booking, make_property


async def test_checkout_must_be_after_checkin(client):
    h = token_for(uuid.uuid4())
    pid = await make_property(client, h)
    r = await make_booking(client, h, pid, "2026-11-05", "2026-11-05")
    assert r.status_code == 422


async def test_personal_block_creates_no_cleaning(client):
    h = token_for(uuid.uuid4())
    pid = await make_property(client, h)
    r = await make_booking(client, h, pid, source="personal")
    assert r.status_code == 201
    tasks = await client.get("/api/v1/cleaning/tasks?date=2026-11-05", headers=h)
    assert tasks.json() == []


async def test_list_filters_by_property_and_owner(client):
    ha, hb = token_for(uuid.uuid4()), token_for(uuid.uuid4(), "b@test.com")
    p1, p2 = await make_property(client, ha), await make_property(client, ha)
    await make_booking(client, ha, p1)
    await make_booking(client, ha, p2, "2026-12-01", "2026-12-03")
    assert len((await client.get("/api/v1/bookings", headers=ha)).json()) == 2
    only = (await client.get(f"/api/v1/bookings?property_id={p1}", headers=ha)).json()
    assert len(only) == 1 and only[0]["property_id"] == p1
    assert (await client.get("/api/v1/bookings", headers=hb)).json() == []


async def test_delete_booking_and_ownership(client):
    ha, hb = token_for(uuid.uuid4()), token_for(uuid.uuid4(), "b@test.com")
    pid = await make_property(client, ha)
    bid = (await make_booking(client, ha, pid)).json()["id"]
    assert (await client.delete(f"/api/v1/bookings/{bid}", headers=hb)).status_code == 404
    assert (await client.delete(f"/api/v1/bookings/{bid}", headers=ha)).status_code == 204
    assert (await client.delete(f"/api/v1/bookings/{bid}", headers=ha)).status_code == 404
