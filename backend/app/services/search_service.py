from supabase import AsyncClient
from app.schemas.schemas import SearchQuery, SearchResult, MemoryRead
from app.services.embeddings import embed_text, local_embed_text, memory_to_text
from app.core.config import settings
from app.db.qdrant import search_memories


async def semantic_search(db: AsyncClient, query: SearchQuery, org_id: str) -> SearchResult:
    if settings.EMBEDDING_PROVIDER.lower() != "openai":
        return await local_search(db, query, org_id)

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


async def local_search(db: AsyncClient, query: SearchQuery, org_id: str) -> SearchResult:
    database_query = db.table("memories").select("*").eq("org_id", org_id)
    if query.agent_id:
        database_query = database_query.eq("agent_id", query.agent_id)
    if query.memory_type:
        database_query = database_query.eq("memory_type", query.memory_type.value)
    if query.outcome:
        database_query = database_query.eq("outcome", query.outcome.value)

    result = await database_query.order("created_at", desc=True).execute()
    query_vector = local_embed_text(query.query)
    scored = []
    for record in result.data or []:
        memory_vector = local_embed_text(
            memory_to_text(record["input"], record["output"])
        )
        score = sum(left * right for left, right in zip(query_vector, memory_vector))
        if score >= query.min_score:
            scored.append((score, record))

    scored.sort(key=lambda item: item[0], reverse=True)
    memories = []
    for score, record in scored[:query.top_k]:
        memory = MemoryRead(**record)
        memory.relevance_score = round(score, 4)
        memories.append(memory)

    return SearchResult(
        memories=memories,
        total=len(memories),
        query=query.query,
    )
