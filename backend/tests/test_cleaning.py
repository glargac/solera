import io
import uuid

import pytest

from app.models import Role
from tests.conftest import token_for
from tests.helpers import make_booking, make_property, make_user


@pytest.fixture(autouse=True)
def fake_storage(monkeypatch):
    async def fake_upload(data, content_type, prefix):
        return f"{prefix}/{uuid.uuid4()}.jpg"

    monkeypatch.setattr("app.api.v1.endpoints.cleaning.upload_photo", fake_upload)


async def setup_task(client):
    host, hh = await make_user(Role.host, email="h@test.com")
    pid = await make_property(client, hh)
    await make_booking(client, hh, pid)
    tasks = (await client.get("/api/v1/cleaning/tasks?date=2026-11-05", headers=hh)).json()
    return host, hh, tasks[0]["id"]


def photo(name="a.jpg", ctype="image/jpeg"):
    return ("files", (name, io.BytesIO(b"fake"), ctype))


async def test_complete_requires_three_photos(client):
    _, hh, tid = await setup_task(client)
    r = await client.post(f"/api/v1/cleaning/tasks/{tid}/photos", headers=hh, files=[photo(), photo()])
    assert r.status_code == 200 and r.json()["status"] == "in_progress"
    assert (await client.post(f"/api/v1/cleaning/tasks/{tid}/complete", headers=hh)).status_code == 422
    await client.post(f"/api/v1/cleaning/tasks/{tid}/photos", headers=hh, files=[photo()])
    r = await client.post(f"/api/v1/cleaning/tasks/{tid}/complete", headers=hh)
    assert r.status_code == 200 and r.json()["status"] == "done"


async def test_rejects_non_image(client):
    _, hh, tid = await setup_task(client)
    r = await client.post(f"/api/v1/cleaning/tasks/{tid}/photos", headers=hh, files=[photo("a.pdf", "application/pdf")])
    assert r.status_code == 415


async def test_assign_and_staff_visibility(client):
    host, hh, tid = await setup_task(client)
    staff, sh = await make_user(Role.cleaning_staff, host_id=host.id, email="s@test.com")
    other, oh = await make_user(Role.cleaning_staff, host_id=host.id, email="o@test.com")

    # Antes de asignar, el limpiador no ve nada ni puede acceder
    assert (await client.get("/api/v1/cleaning/tasks?date=2026-11-05", headers=sh)).json() == []
    assert (await client.post(f"/api/v1/cleaning/tasks/{tid}/complete", headers=sh)).status_code == 404

    r = await client.put(f"/api/v1/cleaning/tasks/{tid}/assign/{staff.id}", headers=hh)
    assert r.status_code == 200 and r.json()["assigned_to"] == str(staff.id)
    assert len((await client.get("/api/v1/cleaning/tasks?date=2026-11-05", headers=sh)).json()) == 1
    assert (await client.get("/api/v1/cleaning/tasks?date=2026-11-05", headers=oh)).json() == []

    # El limpiador asignado puede subir fotos
    r = await client.post(f"/api/v1/cleaning/tasks/{tid}/photos", headers=sh, files=[photo()])
    assert r.status_code == 200


async def test_only_host_can_assign_and_only_own_staff(client):
    host, hh, tid = await setup_task(client)
    staff, sh = await make_user(Role.cleaning_staff, host_id=host.id, email="s@test.com")
    stranger, _ = await make_user(Role.cleaning_staff, host_id=None, email="x@test.com")
    assert (await client.put(f"/api/v1/cleaning/tasks/{tid}/assign/{staff.id}", headers=sh)).status_code == 403
    assert (await client.put(f"/api/v1/cleaning/tasks/{tid}/assign/{stranger.id}", headers=hh)).status_code == 404


async def test_guest_role_cannot_list_tasks(client):
    _, gh = await make_user(Role.guest, email="g@test.com")
    assert (await client.get("/api/v1/cleaning/tasks", headers=gh)).status_code == 403
