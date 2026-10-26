import datetime as dt
import os
import uuid

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import ASGITransport, AsyncClient
from jose import jwk, jwt
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.core import database, security
from app.main import app

KID = "test-key"


def _pem(key, public: bool) -> str:
    if public:
        return key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    return key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


_EC = ec.generate_private_key(ec.SECP256R1())
PRIVATE_PEM = _pem(_EC, False)
PUBLIC_JWK = {**jwk.construct(_pem(_EC, True), "ES256").to_dict(), "kid": KID}


def token_for(user_id: uuid.UUID, email: str = "a@test.com", kid: str = KID) -> dict:
    t = jwt.encode(
        {"sub": str(user_id), "email": email, "aud": "authenticated",
         "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)},
        PRIVATE_PEM, algorithm="ES256", headers={"kid": kid},
    )
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(autouse=True)
def fake_jwks(monkeypatch):
    async def refresh():
        security._jwks.clear()
        security._jwks[KID] = PUBLIC_JWK

    security._jwks.clear()
    monkeypatch.setattr(security, "_refresh_jwks", refresh)


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    database.engine = engine
    database.async_session.configure(bind=engine)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c
