from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.schemas import MemoryCreate, MemoryRead, OutcomeStatus
from app.services import memory_service
from app.core.deps import get_db, get_org_id
from typing import List, Optional

router = APIRouter()


@router.post("/", response_model=MemoryRead, status_code=201)
async def store_memory(memory_in: MemoryCreate, db=Depends(get_db), org_id: str = Depends(get_org_id)):
    return await memory_service.create_memory(db, memory_in, org_id)


@router.get("/", response_model=List[MemoryRead])
async def list_memories(
    agent_id: Optional[str] = Query(None), memory_type: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0), db=Depends(get_db), org_id: str = Depends(get_org_id),
):
    return await memory_service.list_memories(db, org_id, agent_id, memory_type, outcome, limit, offset)


@router.get("/{memory_id}", response_model=MemoryRead)
async def get_memory(memory_id: str, db=Depends(get_db), org_id: str = Depends(get_org_id)):
    memory = await memory_service.get_memory(db, memory_id, org_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.patch("/{memory_id}/outcome", response_model=MemoryRead)
async def update_outcome(memory_id: str, outcome: OutcomeStatus, db=Depends(get_db), org_id: str = Depends(get_org_id)):
    memory = await memory_service.update_outcome(db, memory_id, org_id, outcome)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return memory


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: str, db=Depends(get_db), org_id: str = Depends(get_org_id)):
    deleted = await memory_service.remove_memory(db, memory_id, org_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
