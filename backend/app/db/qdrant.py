from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, ScoredPoint
)
from app.core.config import settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

_client: Optional[AsyncQdrantClient] = None


def get_qdrant() -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
    return _client


async def init_qdrant():
    client = get_qdrant()
    collections = await client.get_collections()
    existing = [c.name for c in collections.collections]

    if settings.QDRANT_COLLECTION not in existing:
        await client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )
        logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION}")
    else:
        logger.info(f"Qdrant collection exists: {settings.QDRANT_COLLECTION}")


async def upsert_memory(memory_id: str, vector: List[float], payload: Dict[str, Any]):
    client = get_qdrant()
    await client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=[PointStruct(id=memory_id, vector=vector, payload=payload)],
    )


async def search_memories(
    query_vector: List[float],
    top_k: int = 5,
    min_score: float = 0.5,
    filters: Optional[Dict[str, Any]] = None,
) -> List[ScoredPoint]:
    client = get_qdrant()

    qdrant_filter = None
    if filters:
        conditions = [
            FieldCondition(key=k, match=MatchValue(value=v))
            for k, v in filters.items() if v is not None
        ]
        if conditions:
            qdrant_filter = Filter(must=conditions)

    results = await client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=min_score,
        query_filter=qdrant_filter,
        with_payload=True,
    )
    return results


async def delete_memory(memory_id: str):
    client = get_qdrant()
    await client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=[memory_id],
    )
