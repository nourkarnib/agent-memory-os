from fastapi import HTTPException
from openai import AsyncOpenAI, APIError, APIConnectionError, AuthenticationError
from app.core.config import settings
from typing import List, Dict, Any
import hashlib
import json
import math
import re

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
    if settings.EMBEDDING_PROVIDER.lower() != "openai":
        return local_embed_text(text)
    if not settings.OPENAI_API_KEY:
        return local_embed_text(text)

    client = get_openai()
    try:
        response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text[:8000],
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=503,
            detail="The configured OPENAI_API_KEY was rejected by OpenAI.",
        ) from exc
    except (APIConnectionError, APIError) as exc:
        raise HTTPException(
            status_code=503,
            detail="The embedding provider is currently unavailable.",
        ) from exc
    return response.data[0].embedding


def local_embed_text(text: str) -> List[float]:
    """Create a deterministic, dependency-free vector for free/demo deployments."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    vector = [0.0] * settings.EMBEDDING_DIM

    for token in tokens:
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % settings.EMBEDDING_DIM
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign

    for left, right in zip(tokens, tokens[1:]):
        phrase = f"{left}:{right}".encode()
        digest = hashlib.blake2b(phrase, digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % settings.EMBEDDING_DIM
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += 0.5 * sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude:
        return [value / magnitude for value in vector]
    return vector


async def embed_memory(input_data: Dict[str, Any], output_data: Dict[str, Any]) -> List[float]:
    text = memory_to_text(input_data, output_data)
    return await embed_text(text)
