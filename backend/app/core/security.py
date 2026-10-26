import uuid

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.database import get_session
from app.models.user import Role, User

bearer = HTTPBearer()


ALLOWED_ALGS = ["ES256", "RS256"]
_jwks: dict[str, dict] = {}  # kid -> JWK


async def _refresh_jwks() -> None:
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    _jwks.clear()
    _jwks.update({k["kid"]: k for k in resp.json()["keys"]})


async def decode_token(token: str) -> dict:
    """Valida el JWT de Supabase con las claves públicas del endpoint JWKS."""
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if header.get("alg") not in ALLOWED_ALGS or not kid:
            raise JWTError("Algoritmo o kid no permitido")
        if kid not in _jwks:  # primera vez o rotación de claves
            await _refresh_jwks()
        if kid not in _jwks:
            raise JWTError("kid desconocido")
        return jwt.decode(
            token, _jwks[kid], algorithms=ALLOWED_ALGS, audience="authenticated"
        )
    except (JWTError, httpx.HTTPError, KeyError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido") from exc


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    claims = await decode_token(creds.credentials)
    user_id = uuid.UUID(claims["sub"])
    user = await session.get(User, user_id)
    if user is None:
        # Primer acceso: crea el perfil como anfitrión.
        user = User(id=user_id, email=claims.get("email", ""), role=Role.host)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


def require_role(*roles: Role):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permiso denegado")
        return user

    return checker
