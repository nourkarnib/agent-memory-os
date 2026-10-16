from supabase import AsyncClient
from app.schemas.schemas import SearchQuery, SearchResult, MemoryRead
from app.services.embeddings import embed_text, local_embed_text, memory_to_text
from app.core.config import settings
from app.db.qdrant import search_memories
from datetime import datetime, timezone
import math
import re


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _lexical_score(query: str, record: dict) -> float:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0.0
    searchable = memory_to_text(record["input"], record["output"])
    searchable += " " + " ".join(record.get("tags") or [])
    return len(query_tokens & _tokens(searchable)) / len(query_tokens)


def _outcome_score(record: dict) -> float:
    return {
        "success": 1.0,
        "pending": 0.5,
        "escalated": 0.5,
        "failure": 0.2,
    }.get(record.get("outcome"), 0.5)


def _recency_score(record: dict) -> float:
    created_at = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
    age_days = max(
        0.0,
        (datetime.now(timezone.utc) - created_at).total_seconds() / 86400,
    )
    return math.exp(-age_days / 90)


def _rerank(query: str, candidates: list[tuple[float, dict]], limit: int) -> list[MemoryRead]:
    ranked = []
    for semantic_score, record in candidates:
        keyword_score = _lexical_score(query, record)
        outcome_score = _outcome_score(record)
        recency_score = _recency_score(record)
        final_score = (
            0.65 * semantic_score
            + 0.20 * keyword_score
            + 0.10 * outcome_score
            + 0.05 * recency_score
        )
        memory = MemoryRead(**record)
        memory.relevance_score = round(final_score, 4)
        memory.retrieval_debug = {
            "semantic": round(semantic_score, 4),
            "keyword": round(keyword_score, 4),
            "outcome": round(outcome_score, 4),
            "recency": round(recency_score, 4),
        }
        ranked.append(memory)

    ranked.sort(key=lambda memory: memory.relevance_score or 0, reverse=True)
    return ranked[:limit]


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
        query_vector=query_vector, top_k=min(query.top_k * 4, 50), min_score=0.0, filters=filters,
    )

    if not hits:
        return SearchResult(memories=[], total=0, query=query.query)

    memory_ids = [hit.id for hit in hits]
    score_map = {hit.id: hit.score for hit in hits}

    result = await db.table("memories").select("*").in_("id", memory_ids).execute()

    candidates = [
        (score_map.get(record["id"], 0.0), record)
        for record in result.data
    ]
    memories = [
        memory for memory in _rerank(query.query, candidates, query.top_k)
        if (memory.relevance_score or 0.0) >= query.min_score
    ]

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

    memories = [
        memory for memory in _rerank(query.query, scored, query.top_k)
        if (memory.relevance_score or 0.0) >= query.min_score
    ]

    return SearchResult(
        memories=memories,
        total=len(memories),
        query=query.query,
    )
