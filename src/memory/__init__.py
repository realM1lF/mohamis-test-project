"""4-Schichten Gedächtnis-System für Mohami.

Schichten:
1. Short Term (InMemoryBuffer) - Aktive Session-Daten
2. Session (RedisMemory) - Chat-History, Session-State
3. Long Term (ChromaLongTermMemory) - Code-Patterns, Solutions
4. Episodic (EpisodicMemory) - Ticket-Resolutionen, Learnings

Unified:
- UnifiedMemoryManager - Verbindet alle Schichten
"""

from .short_term import InMemoryBuffer, ReasoningStep
from .session_redis import RedisMemory, CustomerIsolationViolation
from .long_term_chroma import ChromaLongTermMemory
from .episodic_db import EpisodicMemory, TicketResolution
from .unified_manager import (
    UnifiedMemoryManager,
    LearningEpisode,
    MemoryConfig
)

__all__ = [
    # Schicht 1: Short Term
    "InMemoryBuffer",
    "ReasoningStep",
    
    # Schicht 2: Session
    "RedisMemory",
    "CustomerIsolationViolation",
    
    # Schicht 3: Long Term
    "ChromaLongTermMemory",
    
    # Schicht 4: Episodic
    "EpisodicMemory",
    "TicketResolution",
    
    # Unified
    "UnifiedMemoryManager",
    "LearningEpisode",
    "MemoryConfig",
]
