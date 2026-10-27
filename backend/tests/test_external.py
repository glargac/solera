import uuid

import httpx
import pytest
from sqlmodel import select

from app.core import database, security
from app.models import Booking, Property, User
from app.services import ical_sync, storage
from tests.conftest import KID, PUBLIC_JWK, token_for
from tests.helpers import make_property
from tests.test_ical_sync import ics

REAL_CLIENT = httpx.AsyncClient


def mock_http(monkeypatch, module, handler):
    """Sustituye httpx.AsyncClient en `module` por uno con transporte simulado."""
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        module.httpx, "AsyncClient",
        lambda **kw: REAL_CLIENT(transport=transport, **{k: v for k, v in kw.items() if k != "transport"}),
    )


async def test_sync_endpoint_downloads_ical(client, monkeypatch):
    mock_http(monkeypatch, __import__("app.api.v1.endpoints.properties", fromlist=["x"]),
              lambda req: httpx.Response(200, content=ics()))
    h = token_for(uuid.uuid4())
    pid = await make_property(client, h, ical_url="http://cal/x.ics")
    r = await client.post(f"/api/v1/properties/{pid}/sync", headers=h)
    assert r.status_code == 200 and r.json() == {"synced": 1}
    assert len((await client.get("/api/v1/bookings", headers=h)).json()) == 1


async def test_sync_all_continues_after_failure(client, monkeypatch):
    def handler(req):
        if "bad" in str(req.url):
            return httpx.Response(500)
        return httpx.Response(200, content=ics())

    mock_http(monkeypatch, ical_sync, handler)
    owner = uuid.uuid4()
    async with database.async_session() as s:
        s.add(User(id=owner, email="o@test.com"))
        await s.commit()
        s.add(Property(owner_id=owner, name="Mala", ical_url="http://bad/cal.ics"))
        s.add(Property(owner_id=owner, name="Buena", ical_url="http://ok/cal.ics"))
        s.add(Property(owner_id=owner, name="SinIcal"))
        await s.commit()
    await ical_sync.sync_all()
    async with database.async_session() as s:
        assert len((await s.exec(select(Booking))).all()) == 1


async def test_upload_photo_sends_service_key(monkeypatch):
    seen = {}

    def handler(req):
        seen["url"], seen["auth"], seen["ct"] = str(req.url), req.headers["authorization"], req.headers["content-type"]
        return httpx.Response(200, json={})

    mock_http(monkeypatch, storage, handler)
    monkeypatch.setattr(storage.settings, "supabase_service_key", "KEY")
    path = await storage.upload_photo(b"x", "image/png", "tasks/1")
    assert path.startswith("tasks/1/") and path.endswith(".png")
    assert seen["url"].endswith(f"/storage/v1/object/cleaning-photos/{path}")
    assert seen["auth"] == "Bearer KEY" and seen["ct"] == "image/png"


async def test_upload_photo_raises_on_error(monkeypatch):
    mock_http(monkeypatch, storage, lambda req: httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError):
        await storage.upload_photo(b"x", "image/jpeg", "p")


async def test_jwks_fetched_when_kid_unknown(monkeypatch):
    calls = []

    def handler(req):
        calls.append(str(req.url))
        return httpx.Response(200, json={"keys": [PUBLIC_JWK]})

    monkeypatch.undo()  # quita el fake de _refresh_jwks del fixture autouse
    mock_http(monkeypatch, security, handler)
    security._jwks.clear()
    claims = await security.decode_token(token_for(uuid.uuid4())["Authorization"].split()[1])
    assert claims["aud"] == "authenticated"
    assert calls == ["https://test.supabase.co/auth/v1/.well-known/jwks.json"]
    # Segunda validación: usa la caché, no vuelve a descargar
    await security.decode_token(token_for(uuid.uuid4())["Authorization"].split()[1])
    assert len(calls) == 1


async def test_jwks_unreachable_gives_401(client, monkeypatch):
    monkeypatch.undo()
    mock_http(monkeypatch, security, lambda req: httpx.Response(500))
    security._jwks.clear()
    r = await client.get("/api/v1/auth/me", headers=token_for(uuid.uuid4()))
    assert r.status_code == 401
