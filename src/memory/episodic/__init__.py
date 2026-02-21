"""Episodic Memory Layer - PostgreSQL with pgvector.

Diese Schicht speichert:
- Vollständige Konversations-Verläufe
- Ticket-Informationen und Historie
- Fehler-Episoden und Lern-Ereignisse
- Gelernte Workflows
- Knowledge Graph (Nodes und Relations)

Lebensdauer: Permanent mit Retention-Policies
"""

from .episodic_store import EpisodicMemoryStore
from .database import get_engine, init_customer_schema
from .models import Conversation, Ticket, Episode, LearnedWorkflow, KnowledgeNode, KnowledgeRelation

__all__ = [
    "EpisodicMemoryStore",
    "get_engine",
    "init_customer_schema",
    "Conversation",
    "Ticket",
    "Episode",
    "LearnedWorkflow",
    "KnowledgeNode",
    "KnowledgeRelation"
]
