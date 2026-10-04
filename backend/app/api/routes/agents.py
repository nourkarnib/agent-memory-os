from fastapi import APIRouter, Depends, HTTPException
from app.schemas.schemas import AgentCreate, AgentRead
from app.core.deps import get_db, get_org_id
from typing import List
import uuid
from datetime import datetime, timezone

router = APIRouter()


@router.post("/", response_model=AgentRead, status_code=201)
async def register_agent(agent_in: AgentCreate, db=Depends(get_db), org_id: str = Depends(get_org_id)):
    record = {
        "id": str(uuid.uuid4()), "org_id": org_id, "name": agent_in.name,
        "description": agent_in.description, "framework": agent_in.framework,
        "metadata": agent_in.metadata, "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.table("agents").insert(record).execute()
    return AgentRead(**result.data[0], memory_count=0)


@router.get("/", response_model=List[AgentRead])
async def list_agents(db=Depends(get_db), org_id: str = Depends(get_org_id)):
    result = await db.table("agents").select("*, memories(count)").eq("org_id", org_id).order("created_at", desc=True).execute()
    agents = []
    for r in result.data:
        count = r.pop("memories", [{}])
        memory_count = count[0].get("count", 0) if count else 0
        agents.append(AgentRead(**r, memory_count=memory_count))
    return agents


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, db=Depends(get_db), org_id: str = Depends(get_org_id)):
    result = await db.table("agents").delete().eq("id", agent_id).eq("org_id", org_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Agent not found")
