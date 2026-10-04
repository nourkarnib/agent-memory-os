"""
agentmemory — Python SDK for Agent Memory OS
pip install agentmemory
"""

from .client import MemoryOS
from .decorators import remember
from .types import Memory, MemoryType, OutcomeStatus, SearchResult

__all__ = ["MemoryOS", "remember", "Memory", "MemoryType", "OutcomeStatus", "SearchResult"]
__version__ = "0.1.0"
