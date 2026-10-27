import uuid

from app.core import database
from app.models import Role, User
from tests.conftest import token_for


async def make_user(role: Role, host_id: uuid.UUID | None = None, email: str = "u@test.com"):
    """Crea un usuario directamente en BD y devuelve (user, headers)."""
    user = User(id=uuid.uuid4(), email=email, role=role, host_id=host_id)
    async with database.async_session() as s:
        s.add(user)
        await s.commit()
    return user, token_for(user.id, email)


async def make_property(client, headers, **extra) -> str:
    r = await client.post("/api/v1/properties", json={"name": "Casa", **extra}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


async def make_booking(client, headers, pid, check_in="2026-11-01", check_out="2026-11-05", **extra):
    r = await client.post("/api/v1/bookings", headers=headers, json={
        "property_id": pid, "check_in": check_in, "check_out": check_out, **extra})
    return r
