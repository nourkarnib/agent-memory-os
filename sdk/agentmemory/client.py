import httpx
import time
from typing import Any, Dict, List, Optional
from .types import Memory, MemoryType, OutcomeStatus, SearchResult


class MemoryOS:
    """
    Client for the Agent Memory OS API.

    Usage:
        from agentmemory import MemoryOS

        memory = MemoryOS(api_key="mem_...", agent_id="my-agent",
                           base_url="https://your-backend.azurecontainerapps.io")

        mem = memory.store(
            input={"task": "Should we approve this discount?"},
            output={"decision": "approve"},
            outcome="success",
        )

        results = memory.search("discount approval for enterprise customers")
    """

    def __init__(self, api_key: str, agent_id: str, base_url: str, timeout: float = 30.0):
        self.api_key = api_key
        self.agent_id = agent_id
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    def store(
        self,
        input: Dict[str, Any],
        output: Dict[str, Any],
        outcome: OutcomeStatus | str = OutcomeStatus.PENDING,
        memory_type: MemoryType | str = MemoryType.EPISODIC,
        metadata: Dict[str, Any] = {},
        tags: List[str] = [],
        tool_calls: List[Dict[str, Any]] = [],
        latency_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
    ) -> Memory:
        payload = {
            "agent_id": self.agent_id,
            "input": input,
            "output": output,
            "outcome": outcome if isinstance(outcome, str) else outcome.value,
            "memory_type": memory_type if isinstance(memory_type, str) else memory_type.value,
            "metadata": metadata,
            "tags": tags,
            "tool_calls": tool_calls,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
        }
        response = self._client.post("/api/v1/memories/", json=payload)
        response.raise_for_status()
        return Memory(**response.json())

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.5,
        memory_type: Optional[MemoryType | str] = None,
        outcome: Optional[OutcomeStatus | str] = None,
    ) -> SearchResult:
        payload = {"query": query, "agent_id": self.agent_id, "top_k": top_k, "min_score": min_score}
        if memory_type:
            payload["memory_type"] = memory_type if isinstance(memory_type, str) else memory_type.value
        if outcome:
            payload["outcome"] = outcome if isinstance(outcome, str) else outcome.value

        response = self._client.post("/api/v1/search/", json=payload)
        response.raise_for_status()
        data = response.json()
        return SearchResult(
            memories=[Memory(**m) for m in data["memories"]],
            total=data["total"],
            query=data["query"],
        )

    def get(self, memory_id: str) -> Memory:
        response = self._client.get(f"/api/v1/memories/{memory_id}")
        response.raise_for_status()
        return Memory(**response.json())

    def update_outcome(self, memory_id: str, outcome: OutcomeStatus | str) -> Memory:
        val = outcome if isinstance(outcome, str) else outcome.value
        response = self._client.patch(f"/api/v1/memories/{memory_id}/outcome", params={"outcome": val})
        response.raise_for_status()
        return Memory(**response.json())

    def delete(self, memory_id: str) -> None:
        response = self._client.delete(f"/api/v1/memories/{memory_id}")
        response.raise_for_status()

    def capture(self, input: Dict[str, Any], tags: List[str] = []):
        return _CaptureContext(self, input, tags)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class _CaptureContext:
    def __init__(self, client: MemoryOS, input: Dict[str, Any], tags: List[str]):
        self._client = client
        self.input = input
        self.output: Dict[str, Any] = {}
        self.outcome: str = "pending"
        self.metadata: Dict[str, Any] = {}
        self.tags = tags
        self._start = None
        self._memory: Optional[Memory] = None

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = int((time.perf_counter() - self._start) * 1000)
        if exc_type is not None:
            self.outcome = "failure"
            self.output = self.output or {"error": str(exc_val)}
        self._memory = self._client.store(
            input=self.input, output=self.output, outcome=self.outcome,
            metadata=self.metadata, tags=self.tags, latency_ms=latency_ms,
        )

    @property
    def memory(self) -> Optional["Memory"]:
        return self._memory
