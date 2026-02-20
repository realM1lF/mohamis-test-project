"""Episodic memory for ticket history and learned lessons."""

import hashlib
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

from .chroma_store import ChromaMemoryStore
from .embeddings import EmbeddingProvider


@dataclass
class Episode:
    """A single episode (interaction) from a ticket."""
    content: str
    ticket_id: str
    customer_id: str
    episode_type: str  # "user_request", "agent_response", "solution", "lesson"
    timestamp: str
    metadata: Dict


class EpisodicMemory:
    """Manages episodic memory for learning from past tickets.
    
    Stores:
    - User requests and context
    - Agent responses
    - Solutions that worked
    - Lessons learned
    """
    
    def __init__(
        self,
        memory_store: ChromaMemoryStore,
        embedding_provider: EmbeddingProvider
    ):
        self.memory_store = memory_store
        self.embeddings = embedding_provider
    
    async def record_episode(
        self,
        customer_id: str,
        ticket_id: str,
        content: str,
        episode_type: str,
        metadata: Dict = None
    ) -> str:
        """Record a new episode.
        
        Args:
            customer_id: Customer identifier
            ticket_id: Ticket ID
            content: Episode content (text)
            episode_type: Type of episode
            metadata: Additional metadata
            
        Returns:
            Episode ID
        """
        # Generate embedding
        embedding = await self.embeddings.embed(content)
        
        # Build metadata
        meta = {
            "customer": customer_id,
            "ticket_id": ticket_id,
            "episode_type": episode_type,
            "timestamp": datetime.utcnow().isoformat(),
            "chunk_type": "episode",
            **(metadata or {})
        }
        
        # Store in ChromaDB (using special collection prefix)
        collection_id = f"{customer_id}_episodes"
        
        episode_id = await self.memory_store.add_memory(
            collection_id,
            content,
            embedding,
            metadata=meta,
            source=f"ticket:{ticket_id}"
        )
        
        return episode_id
    
    async def record_ticket_resolution(
        self,
        customer_id: str,
        ticket_id: str,
        problem: str,
        solution: str,
        success: bool = True
    ):
        """Record the resolution of a ticket as a lesson.
        
        This allows the agent to remember what worked.
        """
        lesson_content = f"""## Problem
{problem}

## Lösung
{solution}

## Ergebnis
{'Erfolgreich' if success else 'Nicht erfolgreich'}
"""
        
        await self.record_episode(
            customer_id=customer_id,
            ticket_id=ticket_id,
            content=lesson_content,
            episode_type="lesson",
            metadata={
                "success": success,
                "problem_summary": problem[:200],
                "solution_summary": solution[:200]
            }
        )
    
    async def find_similar_episodes(
        self,
        customer_id: str,
        query: str,
        episode_type: Optional[str] = None,
        n_results: int = 3
    ) -> List[Dict]:
        """Find similar past episodes.
        
        Args:
            customer_id: Customer to search
            query: Search query (e.g., current ticket description)
            episode_type: Filter by type (optional)
            n_results: Number of results
            
        Returns:
            List of similar episodes with content and metadata
        """
        # Generate query embedding
        query_embedding = await self.embeddings.embed(query)
        
        # Build filter
        filter_meta = None
        if episode_type:
            filter_meta = {"episode_type": episode_type}
        
        # Search in episode collection
        collection_id = f"{customer_id}_episodes"
        
        # Ensure collection exists
        try:
            results = await self.memory_store.search(
                collection_id,
                query_embedding,
                n_results=n_results,
                filter_metadata=filter_meta
            )
        except:
            # Collection might not exist yet
            return []
        
        return results
    
    async def get_relevant_context(
        self,
        customer_id: str,
        current_ticket_description: str,
        n_lessons: int = 2,
        n_episodes: int = 3
    ) -> str:
        """Get relevant past context for a new ticket.
        
        Returns formatted string with:
        - Similar lessons learned
        - Similar past tickets
        """
        parts = []
        
        # Find lessons
        lessons = await self.find_similar_episodes(
            customer_id,
            current_ticket_description,
            episode_type="lesson",
            n_results=n_lessons
        )
        
        if lessons:
            parts.append("## Gelernte Lektionen aus der Vergangenheit")
            for i, lesson in enumerate(lessons, 1):
                parts.append(f"\n### Lektion {i}")
                parts.append(lesson["content"][:500] + "...")
                parts.append("")
        
        # Find similar episodes
        episodes = await self.find_similar_episodes(
            customer_id,
            current_ticket_description,
            n_results=n_episodes
        )
        
        if episodes:
            parts.append("## Ähnliche vergangene Tickets")
            for ep in episodes:
                meta = ep.get("metadata", {})
                ticket_id = meta.get("ticket_id", "unknown")
                parts.append(f"- Ticket {ticket_id}: {ep['content'][:150]}...")
            parts.append("")
        
        return "\n".join(parts) if parts else ""
    
    async def record_conversation_turn(
        self,
        customer_id: str,
        ticket_id: str,
        author: str,
        content: str
    ):
        """Record a single comment/conversation turn.
        
        Lightweight recording for all interactions.
        """
        episode_type = "user_request" if author != "mohami" else "agent_response"
        
        await self.record_episode(
            customer_id=customer_id,
            ticket_id=ticket_id,
            content=content,
            episode_type=episode_type,
            metadata={"author": author}
        )
