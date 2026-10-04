from openai import AsyncOpenAI
from app.core.config import settings
from typing import List, Dict, Any
import json

_client: AsyncOpenAI | None = None


def get_openai() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def memory_to_text(input_data: Dict[str, Any], output_data: Dict[str, Any]) -> str:
    parts = []
    if isinstance(input_data, dict):
        task = input_data.get("task") or input_data.get("prompt") or input_data.get("query") or ""
        if task:
            parts.append(f"Task: {task}")
        context = input_data.get("context", "")
        if context:
            parts.append(f"Context: {context}")
    if isinstance(output_data, dict):
        result = output_data.get("result") or output_data.get("response") or output_data.get("decision") or ""
        if result:
            parts.append(f"Decision: {result}")
        reasoning = output_data.get("reasoning") or output_data.get("explanation") or ""
        if reasoning:
            parts.append(f"Reasoning: {reasoning}")
    if not parts:
        parts = [json.dumps(input_data)[:500], json.dumps(output_data)[:500]]
    return " | ".join(parts)


async def embed_text(text: str) -> List[float]:
    client = get_openai()
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text[:8000],
    )
    return response.data[0].embedding


async def embed_memory(input_data: Dict[str, Any], output_data: Dict[str, Any]) -> List[float]:
    text = memory_to_text(input_data, output_data)
    return await embed_text(text)
