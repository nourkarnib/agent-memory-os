from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
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


class MemoryCreate(BaseModel):
    agent_id: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    memory_type: MemoryType = MemoryType.EPISODIC
    outcome: OutcomeStatus = OutcomeStatus.PENDING
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None


class MemoryRead(BaseModel):
    id: str
    agent_id: str
    org_id: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    memory_type: MemoryType
    outcome: OutcomeStatus
    metadata: Dict[str, Any]
    tags: List[str]
    tool_calls: List[Dict[str, Any]]
    latency_ms: Optional[int]
    tokens_used: Optional[int]
    created_at: datetime
    relevance_score: Optional[float] = None

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    agent_id: Optional[str] = None
    memory_type: Optional[MemoryType] = None
    outcome: Optional[OutcomeStatus] = None
    top_k: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class SearchResult(BaseModel):
    memories: List[MemoryRead]
    total: int
    query: str


class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    framework: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentRead(BaseModel):
    id: str
    org_id: str
    name: str
    description: Optional[str]
    framework: Optional[str]
    metadata: Dict[str, Any]
    memory_count: int = 0
    last_active: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsSummary(BaseModel):
    total_memories: int
    total_agents: int
    memories_today: int
    success_rate: float
    avg_latency_ms: Optional[float]
    top_agents: List[Dict[str, Any]]
    memory_type_breakdown: Dict[str, int]
    outcome_breakdown: Dict[str, int]
    daily_volume: List[Dict[str, Any]]
