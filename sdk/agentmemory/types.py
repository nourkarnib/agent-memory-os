from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class OutcomeStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    ESCALATED = "escalated"


@dataclass
class Memory:
    id: str
    agent_id: str
    org_id: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    memory_type: str
    outcome: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    created_at: Optional[str] = None
    relevance_score: Optional[float] = None


@dataclass
class SearchResult:
    memories: List[Memory]
    total: int
    query: str
