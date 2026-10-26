import uuid
from collections.abc import AsyncIterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings



def _engine_args(url: str) -> tuple[str, dict]:
    """Acepta la URL tal como la da Supabase (postgresql://...?pgbouncer=true)."""
    kwargs: dict = {}
    if url.startswith(("postgres://", "postgresql://")):
        url = "postgresql+asyncpg://" + url.split("://", 1)[1]
    if url.startswith("postgresql+asyncpg://"):
        parts = urlsplit(url)
        query = [(k, v) for k, v in parse_qsl(parts.query) if k != "pgbouncer"]
        url = urlunsplit(parts._replace(query=urlencode(query)))
        # El pooler de Supabase (modo transacción) no admite prepared statements.
        kwargs["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
        }
    return url, kwargs


_url, _kwargs = _engine_args(settings.database_url)
engine = create_async_engine(_url, echo=False, **_kwargs)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session


async def init_db() -> None:
    """Crea tablas en desarrollo. En producción se usa Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
