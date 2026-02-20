"""ChromaDB-based vector store for agent memories."""

import os
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

import chromadb
from chromadb.config import Settings


class ChromaMemoryStore:
    """Vector store for customer memories and context using ChromaDB."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB store.
        
        Args:
            persist_directory: Where to store ChromaDB files
        """
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collection cache
        self._collections = {}
    
    def _get_collection(self, customer_id: str):
        """Get or create collection for a customer."""
        if customer_id not in self._collections:
            collection_name = f"customer_{customer_id}"
            try:
                self._collections[customer_id] = self.client.get_collection(collection_name)
            except ValueError:
                # Collection doesn't exist, create it
                self._collections[customer_id] = self.client.create_collection(
                    name=collection_name,
                    metadata={"customer": customer_id, "type": "memories"}
                )
        return self._collections[customer_id]
    
    def _generate_id(self, content: str, source: str) -> str:
        """Generate unique ID for a memory chunk."""
        hash_input = f"{source}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    async def add_memory(
        self,
        customer_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict = None,
        source: str = "unknown"
    ) -> str:
        """Add a memory to the store.
        
        Args:
            customer_id: Customer identifier
            content: Text content
            embedding: Vector embedding
            metadata: Additional metadata
            source: Source of the memory (e.g., 'context.md', 'conversation')
        
        Returns:
            memory_id: Unique identifier
        """
        collection = self._get_collection(customer_id)
        
        memory_id = self._generate_id(content, source)
        
        doc_metadata = {
            "source": source,
            "created_at": datetime.utcnow().isoformat(),
            "customer": customer_id,
            **(metadata or {})
        }
        
        collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[doc_metadata]
        )
        
        return memory_id
    
    async def add_memories_batch(
        self,
        customer_id: str,
        memories: List[Dict]
    ) -> List[str]:
        """Add multiple memories at once.
        
        Args:
            memories: List of dicts with 'content', 'embedding', 'metadata', 'source'
        
        Returns:
            List of memory IDs
        """
        collection = self._get_collection(customer_id)
        
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for memory in memories:
            memory_id = self._generate_id(memory["content"], memory.get("source", "unknown"))
            ids.append(memory_id)
            embeddings.append(memory["embedding"])
            documents.append(memory["content"])
            metadatas.append({
                "source": memory.get("source", "unknown"),
                "created_at": datetime.utcnow().isoformat(),
                "customer": customer_id,
                **memory.get("metadata", {})
            })
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return ids
    
    async def search(
        self,
        customer_id: str,
        query_embedding: List[float],
        n_results: int = 5,
        filter_metadata: Dict = None
    ) -> List[Dict]:
        """Search memories by similarity.
        
        Args:
            customer_id: Customer to search
            query_embedding: Query vector
            n_results: Number of results
            filter_metadata: Optional metadata filter
        
        Returns:
            List of matching memories with content, metadata, distance
        """
        collection = self._get_collection(customer_id)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )
        
        memories = []
        if results["ids"] and results["ids"][0]:
            for i, memory_id in enumerate(results["ids"][0]):
                memories.append({
                    "id": memory_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
        
        return memories
    
    async def get_all_sources(self, customer_id: str) -> List[str]:
        """Get all unique sources for a customer."""
        collection = self._get_collection(customer_id)
        
        # Get all metadata
        results = collection.get(include=["metadatas"])
        
        sources = set()
        if results["metadatas"]:
            for meta in results["metadatas"]:
                sources.add(meta.get("source", "unknown"))
        
        return list(sources)
    
    async def delete_by_source(self, customer_id: str, source: str):
        """Delete all memories from a specific source."""
        collection = self._get_collection(customer_id)
        
        # Find all IDs with this source
        results = collection.get(
            where={"source": source},
            include=[]
        )
        
        if results["ids"]:
            collection.delete(ids=results["ids"])
    
    async def reset_customer(self, customer_id: str):
        """Delete all memories for a customer."""
        collection_name = f"customer_{customer_id}"
        try:
            self.client.delete_collection(collection_name)
            if customer_id in self._collections:
                del self._collections[customer_id]
        except ValueError:
            pass  # Collection didn't exist
