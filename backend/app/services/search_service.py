from supabase import AsyncClient
from app.schemas.schemas import SearchQuery, SearchResult, MemoryRead
from app.services.embeddings import embed_text
from app.db.qdrant import search_memories


async def semantic_search(db: AsyncClient, query: SearchQuery, org_id: str) -> SearchResult:
    query_vector = await embed_text(query.query)

    filters = {"org_id": org_id}
    if query.agent_id:
        filters["agent_id"] = query.agent_id
    if query.memory_type:
        filters["memory_type"] = query.memory_type.value
    if query.outcome:
        filters["outcome"] = query.outcome.value

    hits = await search_memories(
        query_vector=query_vector, top_k=query.top_k, min_score=query.min_score, filters=filters,
    )

    if not hits:
        return SearchResult(memories=[], total=0, query=query.query)

    memory_ids = [hit.id for hit in hits]
    score_map = {hit.id: hit.score for hit in hits}

    result = await db.table("memories").select("*").in_("id", memory_ids).execute()

    memories = []
    for record in result.data:
        mem = MemoryRead(**record)
        mem.relevance_score = round(score_map.get(record["id"], 0.0), 4)
        memories.append(mem)

    memories.sort(key=lambda m: m.relevance_score or 0, reverse=True)

    return SearchResult(memories=memories, total=len(memories), query=query.query)
