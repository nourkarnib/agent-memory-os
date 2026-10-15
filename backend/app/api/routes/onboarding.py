import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from supabase import AsyncClient

from app.core.deps import get_db
from app.schemas.schemas import OnboardingRequest, OnboardingResponse

router = APIRouter()


@router.post("/signup", response_model=OnboardingResponse, status_code=201)
async def create_workspace(
    onboarding: OnboardingRequest,
    db: AsyncClient = Depends(get_db),
) -> OnboardingResponse:
    organization_name = onboarding.organization_name.strip()
    if not organization_name:
        raise HTTPException(status_code=422, detail="Organization name is required")

    api_key = f"mem_{secrets.token_urlsafe(32)}"
    organization_id = str(uuid.uuid4())

    organization = await db.table("organizations").insert({
        "id": organization_id,
        "name": organization_name,
    }).execute()
    if not organization.data:
        raise HTTPException(status_code=502, detail="Could not create organization")

    key = await db.table("api_keys").insert({
        "org_id": organization_id,
        "name": onboarding.key_name.strip() or "Dashboard",
        "key_hash": hashlib.sha256(api_key.encode()).hexdigest(),
        "key_prefix": api_key[:12],
    }).execute()
    if not key.data:
        raise HTTPException(status_code=502, detail="Could not create API key")

    return OnboardingResponse(
        organization_name=organization_name,
        api_key=api_key,
    )
