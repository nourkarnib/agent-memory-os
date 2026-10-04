from fastapi import APIRouter, Depends
from app.schemas.schemas import SearchQuery, SearchResult
from app.services.search_service import semantic_search
from app.core.deps import get_db, get_org_id

router = APIRouter()


@router.post("/", response_model=SearchResult)
async def search(query: SearchQuery, db=Depends(get_db), org_id: str = Depends(get_org_id)):
    return await semantic_search(db, query, org_id)
