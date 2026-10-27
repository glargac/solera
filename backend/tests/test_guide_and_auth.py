import uuid

from app.models import Role
from tests.conftest import token_for
from tests.helpers import make_booking, make_property, make_user


async def test_me_creates_host_profile(client):
    uid = uuid.uuid4()
    r = await client.get("/api/v1/auth/me", headers=token_for(uid, "new@test.com"))
    assert r.status_code == 200
    assert r.json()["role"] == "host" and r.json()["email"] == "new@test.com"


async def test_guest_cannot_use_host_endpoints(client):
    _, gh = await make_user(Role.guest, email="g@test.com")
    assert (await client.get("/api/v1/properties", headers=gh)).status_code == 403
    assert (await client.get("/api/v1/bookings", headers=gh)).status_code == 403


async def test_guide_unknown_token(client):
    assert (await client.get("/api/v1/guests/guide/nope")).status_code == 404


async def test_guide_exposes_only_guest_safe_fields(client):
    h = token_for(uuid.uuid4())
    pid = await make_property(client, h, wifi_name="net", wifi_password="pw", nightly_price=300)
    token = (await make_booking(client, h, pid, guest_name="Ana")).json()["guide_token"]
    data = (await client.get(f"/api/v1/guests/guide/{token}")).json()
    assert data["wifi_name"] == "net" and data["guest_name"] == "Ana"
    for private in ("nightly_price", "owner_id", "ical_url", "cleaning_fee", "id"):
        assert private not in data


async def test_tokens_are_unique_per_booking(client):
    h = token_for(uuid.uuid4())
    pid = await make_property(client, h)
    t1 = (await make_booking(client, h, pid)).json()["guide_token"]
    t2 = (await make_booking(client, h, pid, "2026-12-01", "2026-12-03")).json()["guide_token"]
    assert t1 != t2
