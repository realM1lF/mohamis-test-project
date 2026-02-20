"""Customer context manager for loading and indexing memories."""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from .chroma_store import ChromaMemoryStore
from .embeddings import EmbeddingProvider


@dataclass
class MemoryChunk:
    """A chunk of memory with metadata."""
    content: str
    source: str  # e.g., "context.md", "history.md"
    chunk_type: str  # e.g., "project_info", "tech_stack", "lesson"
    metadata: Dict


class CustomerContextManager:
    """Manages customer context by loading and indexing memory files.
    
    Structure:
        agents/{agent_id}/customers/{customer_id}/
            context.md      - Project overview, tech stack
            tech-stack.md   - Technical details
            history.md      - Learned lessons, past decisions
            contacts.md     - Key people and roles
    """
    
    def __init__(
        self,
        agent_id: str,
        memory_store: ChromaMemoryStore,
        embedding_provider: EmbeddingProvider,
        base_path: str = "./agents"
    ):
        self.agent_id = agent_id
        self.memory_store = memory_store
        self.embeddings = embedding_provider
        self.base_path = Path(base_path) / agent_id / "customers"
        
        # Track which customers have been indexed
        self._indexed_customers = set()
    
    async def ensure_indexed(self, customer_id: str) -> bool:
        """Ensure customer memories are indexed. Load if not already done.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            True if indexed successfully
        """
        if customer_id in self._indexed_customers:
            return True
        
        customer_path = self.base_path / customer_id
        if not customer_path.exists():
            print(f"No memory folder for customer {customer_id}")
            return False
        
        # Load all memory files
        memories = await self._load_customer_memories(customer_path, customer_id)
        
        if not memories:
            print(f"No memories found for {customer_id}")
            return False
        
        # Generate embeddings and store
        await self._index_memories(customer_id, memories)
        
        self._indexed_customers.add(customer_id)
        print(f"Indexed {len(memories)} memories for {customer_id}")
        return True
    
    async def _load_customer_memories(
        self,
        customer_path: Path,
        customer_id: str
    ) -> List[MemoryChunk]:
        """Load all memory files for a customer."""
        memories = []
        
        # Define memory files and their types
        memory_files = {
            "context.md": "project_info",
            "tech-stack.md": "tech_stack",
            "history.md": "lessons_learned",
            "contacts.md": "contacts",
            "preferences.md": "preferences",
        }
        
        for filename, chunk_type in memory_files.items():
            file_path = customer_path / filename
            if file_path.exists():
                chunks = await self._parse_memory_file(
                    file_path, filename, chunk_type, customer_id
                )
                memories.extend(chunks)
        
        return memories
    
    async def _parse_memory_file(
        self,
        file_path: Path,
        source: str,
        chunk_type: str,
        customer_id: str
    ) -> List[MemoryChunk]:
        """Parse a memory file into chunks."""
        content = file_path.read_text(encoding="utf-8")
        
        # Split by sections (## headings)
        sections = self._split_by_sections(content)
        
        chunks = []
        for section in sections:
            # Further split large sections
            sub_chunks = self._chunk_section(section, max_chars=1000)
            
            for chunk_text in sub_chunks:
                chunks.append(MemoryChunk(
                    content=chunk_text,
                    source=source,
                    chunk_type=chunk_type,
                    metadata={
                        "customer": customer_id,
                        "file": source,
                        "type": chunk_type,
                    }
                ))
        
        return chunks
    
    def _split_by_sections(self, content: str) -> List[str]:
        """Split markdown content by ## headings."""
        # Split by ## but keep the heading
        pattern = r'(?=\n## )'
        sections = re.split(pattern, content)
        
        # Clean up
        sections = [s.strip() for s in sections if s.strip()]
        return sections
    
    def _chunk_section(self, section: str, max_chars: int = 1000) -> List[str]:
        """Split large sections into smaller chunks."""
        if len(section) <= max_chars:
            return [section]
        
        chunks = []
        lines = section.split('\n')
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            
            if current_length + line_length > max_chars and current_chunk:
                # Save current chunk
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    async def _index_memories(
        self,
        customer_id: str,
        memories: List[MemoryChunk]
    ):
        """Generate embeddings and store memories."""
        # Prepare batch
        memory_data = []
        
        for memory in memories:
            embedding = await self.embeddings.embed(memory.content)
            memory_data.append({
                "content": memory.content,
                "embedding": embedding,
                "source": memory.source,
                "metadata": {
                    **memory.metadata,
                    "chunk_type": memory.chunk_type,
                }
            })
        
        # Store in ChromaDB
        await self.memory_store.add_memories_batch(customer_id, memory_data)
    
    async def search_context(
        self,
        customer_id: str,
        query: str,
        n_results: int = 3,
        chunk_type: Optional[str] = None
    ) -> List[Dict]:
        """Search customer context for relevant information.
        
        Args:
            customer_id: Customer to search
            query: Search query
            n_results: Number of results
            chunk_type: Optional filter by type (e.g., "tech_stack")
            
        Returns:
            List of relevant memories with content and metadata
        """
        # Ensure indexed
        await self.ensure_indexed(customer_id)
        
        # Generate query embedding
        query_embedding = await self.embeddings.embed(query)
        
        # Build filter
        filter_metadata = None
        if chunk_type:
            filter_metadata = {"chunk_type": chunk_type}
        
        # Search
        results = await self.memory_store.search(
            customer_id,
            query_embedding,
            n_results=n_results,
            filter_metadata=filter_metadata
        )
        
        return results
    
    async def get_context_summary(self, customer_id: str) -> str:
        """Get a summary of customer context for system prompt.
        
        Returns formatted string with key information.
        """
        await self.ensure_indexed(customer_id)
        
        # Search for general project info
        project_info = await self.search_context(
            customer_id,
            "Projekt Übersicht Beschreibung",
            n_results=2,
            chunk_type="project_info"
        )
        
        # Search for tech stack
        tech_info = await self.search_context(
            customer_id,
            "Technologie Stack Framework",
            n_results=2,
            chunk_type="tech_stack"
        )
        
        # Build summary
        parts = [f"## Kunden-Kontext: {customer_id}\n"]
        
        if project_info:
            parts.append("### Projekt")
            for info in project_info:
                parts.append(info["content"][:300] + "...")
            parts.append("")
        
        if tech_info:
            parts.append("### Technologie-Stack")
            for info in tech_info:
                parts.append(f"- {info['content'][:200]}...")
            parts.append("")
        
        return "\n".join(parts)
    
    async def add_lesson_learned(
        self,
        customer_id: str,
        lesson: str,
        context: str = ""
    ):
        """Add a learned lesson to the customer's history.
        
        This allows the agent to remember what worked/didn't work.
        """
        content = f"## Gelernte Lektion\n\n{lesson}"
        if context:
            content += f"\n\nKontext: {context}"
        
        embedding = await self.embeddings.embed(content)
        
        await self.memory_store.add_memory(
            customer_id,
            content,
            embedding,
            metadata={
                "customer": customer_id,
                "type": "lessons_learned",
                "chunk_type": "lessons_learned",
                "source": "runtime_learning",
            },
            source="runtime_learning"
        )
    
    def invalidate_cache(self, customer_id: str):
        """Force re-indexing next time."""
        if customer_id in self._indexed_customers:
            self._indexed_customers.remove(customer_id)
