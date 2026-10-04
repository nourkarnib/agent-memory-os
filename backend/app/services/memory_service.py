from supabase import AsyncClient
from app.schemas.schemas import MemoryCreate, MemoryRead, OutcomeStatus
from app.services.embeddings import embed_memory
from app.db.qdrant import upsert_memory, delete_memory
from datetime import datetime, timezone
from typing import List, Optional
import uuid


async def create_memory(db: AsyncClient, memory_in: MemoryCreate, org_id: str) -> MemoryRead:
    memory_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    vector = await embed_memory(memory_in.input, memory_in.output)

    record = {
        "id": memory_id,
        "org_id": org_id,
        "agent_id": memory_in.agent_id,
        "input": memory_in.input,
        "output": memory_in.output,
        "memory_type": memory_in.memory_type.value,
        "outcome": memory_in.outcome.value,
        "metadata": memory_in.metadata,
        "tags": memory_in.tags,
        "tool_calls": memory_in.tool_calls,
        "latency_ms": memory_in.latency_ms,
        "tokens_used": memory_in.tokens_used,
        "created_at": now,
    }

    await db.table("memories").insert(record).execute()

    await upsert_memory(
        memory_id=memory_id,
        vector=vector,
        payload={
            "org_id": org_id,
            "agent_id": memory_in.agent_id,
            "memory_type": memory_in.memory_type.value,
            "outcome": memory_in.outcome.value,
            "created_at": now,
        },
    )

    return MemoryRead(**record)


async def get_memory(db: AsyncClient, memory_id: str, org_id: str) -> Optional[MemoryRead]:
    result = await db.table("memories").select("*").eq("id", memory_id).eq("org_id", org_id).single().execute()
    if result.data:
        return MemoryRead(**result.data)
    return None


async def list_memories(
    db: AsyncClient, org_id: str, agent_id: Optional[str] = None,
    memory_type: Optional[str] = None, outcome: Optional[str] = None,
    limit: int = 50, offset: int = 0,
) -> List[MemoryRead]:
    query = db.table("memories").select("*").eq("org_id", org_id)
    if agent_id:
        query = query.eq("agent_id", agent_id)
    if memory_type:
        query = query.eq("memory_type", memory_type)
    if outcome:
        query = query.eq("outcome", outcome)
    result = await query.order("created_at", desc=True).limit(limit).offset(offset).execute()
    return [MemoryRead(**r) for r in result.data]


async def update_outcome(db: AsyncClient, memory_id: str, org_id: str, outcome: OutcomeStatus) -> Optional[MemoryRead]:
    result = await db.table("memories").update({"outcome": outcome.value}).eq("id", memory_id).eq("org_id", org_id).execute()
    if result.data:
        return MemoryRead(**result.data[0])
    return None


async def remove_memory(db: AsyncClient, memory_id: str, org_id: str) -> bool:
    result = await db.table("memories").delete().eq("id", memory_id).eq("org_id", org_id).execute()
    if result.data:
        await delete_memory(memory_id)
        return True
    return False
