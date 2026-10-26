import uuid

import httpx

from app.core.config import settings


async def upload_photo(data: bytes, content_type: str, prefix: str) -> str:
    """Sube a Supabase Storage y devuelve la ruta del objeto."""
    ext = "png" if content_type == "image/png" else "jpg"
    path = f"{prefix}/{uuid.uuid4()}.{ext}"
    url = f"{settings.supabase_url}/storage/v1/object/{settings.supabase_storage_bucket}/{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            content=data,
            headers={
                "Authorization": f"Bearer {settings.supabase_service_key}",
                "Content-Type": content_type,
            },
        )
        resp.raise_for_status()
    return path
