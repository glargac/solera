import uuid

from tests.conftest import token_for
from tests.helpers import make_property


async def test_crud_cycle(client):
    h = token_for(uuid.uuid4())
    pid = await make_property(client, h, city="Marbella", nightly_price=150)
    props = (await client.get("/api/v1/properties", headers=h)).json()
    assert [p["city"] for p in props] == ["Marbella"]

    r = await client.put(f"/api/v1/properties/{pid}", headers=h, json={"name": "Nueva", "wifi_name": "wifi"})
    assert r.status_code == 200 and r.json()["name"] == "Nueva" and r.json()["wifi_name"] == "wifi"

    assert (await client.delete(f"/api/v1/properties/{pid}", headers=h)).status_code == 204
    assert (await client.get("/api/v1/properties", headers=h)).json() == []


async def test_other_host_cannot_touch_property(client):
    ha, hb = token_for(uuid.uuid4()), token_for(uuid.uuid4(), "b@test.com")
    pid = await make_property(client, ha)
    assert (await client.put(f"/api/v1/properties/{pid}", headers=hb, json={"name": "x"})).status_code == 404
    assert (await client.delete(f"/api/v1/properties/{pid}", headers=hb)).status_code == 404
    assert (await client.post(f"/api/v1/properties/{pid}/sync", headers=hb)).status_code == 404


async def test_sync_requires_ical_url(client):
    h = token_for(uuid.uuid4())
    pid = await make_property(client, h)
    assert (await client.post(f"/api/v1/properties/{pid}/sync", headers=h)).status_code == 400


async def test_missing_name_is_rejected(client):
    h = token_for(uuid.uuid4())
    assert (await client.post("/api/v1/properties", json={}, headers=h)).status_code == 422
