from fastapi import Header, HTTPException
from supabase import AsyncClient, create_async_client
from app.core.config import settings
from typing import Optional
import hashlib


async def get_db() -> AsyncClient:
    return await create_async_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


async def get_org_id(x_api_key: Optional[str] = Header(None)) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required. Pass X-Api-Key header.")

    db = await get_db()
    result = await db.table("api_keys").select("org_id, is_active").eq("key_hash", _hash_key(x_api_key)).single().execute()

    if not result.data or not result.data.get("is_active"):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    await db.table("api_keys").update({"last_used": "now()"}).eq("key_hash", _hash_key(x_api_key)).execute()

    return result.data["org_id"]


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
