"""Schicht 3: Long Term Memory (ChromaDB).

Diese Schicht speichert:
- Code-Patterns und Best Practices
- Wiederverwendbare Lösungen
- Dokumentation und Wissen
- Konversations-Zusammenfassungen

Lebensdauer: Permanent
Collections pro Kunde: customer_{customer_id}_{type}
"""

import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import chromadb
from chromadb.config import Settings


class PatternType(str, Enum):
    """Typen von Code-Patterns."""
    REPOSITORY_DECORATOR = "repository_decorator"
    SUBSCRIBER = "subscriber"
    SERVICE = "service"
    CONTROLLER = "controller"
    CART_PROCESSOR = "cart_processor"
    TWIG_EXTENSION = "twig_extension"
    CUSTOM_FIELD = "custom_field"
    MIGRATION = "migration"
    EVENT_LISTENER = "event_listener"
    COMMAND = "command"
    SCHEDULED_TASK = "scheduled_task"


class SolutionType(str, Enum):
    """Typen von Lösungen."""
    BUGFIX = "bugfix"
    FEATURE = "feature"
    OPTIMIZATION = "optimization"
    CONFIGURATION = "configuration"
    MIGRATION = "migration"
    SECURITY = "security"


class DocType(str, Enum):
    """Typen von Dokumentation."""
    API = "api"
    ARCHITECTURE = "architecture"
    PROCESS = "process"
    SETUP = "setup"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class CodePattern:
    """Ein erkanntes Code-Pattern."""
    id: str
    code_snippet: str
    file_path: str
    pattern_type: PatternType
    shopware_version: str
    language: str = "php"
    success_rate: float = 1.0
    usage_count: int = 0
    source_ticket: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class Solution:
    """Eine erfolgreiche Problemlösung."""
    id: str
    ticket_id: str
    problem_description: str
    solution_description: str
    code_changes: Optional[str] = None
    solution_type: SolutionType = SolutionType.BUGFIX
    affected_files: List[str] = None
    shopware_version: Optional[str] = None
    plugins: List[str] = None
    verified: bool = False
    resolution_time_hours: Optional[float] = None
    agent_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.affected_files is None:
            self.affected_files = []
        if self.plugins is None:
            self.plugins = []


class ChromaLongTermMemory:
    """ChromaDB-basiertes Langzeit-Gedächtnis.
    
    Verwaltet mehrere Collections pro Kunde:
    - {customer_id}_code_patterns: Code-Patterns und Best Practices
    - {customer_id}_solutions: Erfolgreiche Problem-Lösungen
    - {customer_id}_documentation: Projekt-spezifische Dokumentation
    - {customer_id}_conversations: Konversations-Zusammenfassungen
    """
    
    # Collection Suffixe
    COLLECTION_PATTERNS = "code_patterns"
    COLLECTION_SOLUTIONS = "solutions"
    COLLECTION_DOCUMENTATION = "documentation"
    COLLECTION_CONVERSATIONS = "conversations"
    
    def __init__(
        self,
        chroma_client: chromadb.Client,
        customer_id: str,
        embedding_function = None
    ):
        """Initialize Long Term Memory.
        
        Args:
            chroma_client: ChromaDB client
            customer_id: Customer identifier
            embedding_function: Optional custom embedding function
        """
        self.client = chroma_client
        self.customer_id = customer_id
        self._embedding_function = embedding_function
        
        # Collection cache
        self._collections: Dict[str, chromadb.Collection] = {}
    
    def _get_collection_name(self, collection_type: str) -> str:
        """Erstellt Collection-Name mit Kunden-Isolation."""
        safe_customer = self._sanitize_customer_id(self.customer_id)
        return f"customer_{safe_customer}_{collection_type}"
    
    def _sanitize_customer_id(self, customer_id: str) -> str:
        """Sanitizes customer_id für Collection-Namen (nur alphanumerisch + underscore)."""
        import re
        return re.sub(r'[^a-zA-Z0-9_]', '_', customer_id)
    
    def _get_collection(self, collection_type: str) -> chromadb.Collection:
        """Get or create collection."""
        if collection_type not in self._collections:
            collection_name = self._get_collection_name(collection_type)
            
            try:
                self._collections[collection_type] = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self._embedding_function
                )
            except ValueError:
                # Collection doesn't exist, create it
                self._collections[collection_type] = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "customer": self.customer_id,
                        "type": collection_type,
                        "created_at": datetime.utcnow().isoformat()
                    },
                    embedding_function=self._embedding_function
                )
        
        return self._collections[collection_type]
    
    # === Code Patterns ===
    
    async def store_pattern(
        self,
        code_snippet: str,
        file_path: str,
        pattern_type: PatternType,
        shopware_version: str,
        language: str = "php",
        source_ticket: Optional[str] = None,
        pattern_id: Optional[str] = None
    ) -> str:
        """Speichert ein Code-Pattern.
        
        Args:
            code_snippet: Der Code
            file_path: Pfad zur Datei
            pattern_type: Art des Patterns
            shopware_version: Shopware-Version
            language: Programmiersprache
            source_ticket: Ursprüngliches Ticket
            pattern_id: Optional custom ID
            
        Returns:
            Pattern ID
        """
        collection = self._get_collection(self.COLLECTION_PATTERNS)
        
        # Generate ID
        if pattern_id is None:
            import hashlib
            pattern_id = hashlib.md5(
                f"{file_path}:{code_snippet[:100]}".encode()
            ).hexdigest()
        
        metadata = {
            "file_path": file_path,
            "pattern_type": pattern_type.value if isinstance(pattern_type, PatternType) else pattern_type,
            "language": language,
            "shopware_version": shopware_version,
            "success_rate": 1.0,
            "usage_count": 0,
            "source_ticket": source_ticket or "",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        collection.add(
            ids=[pattern_id],
            documents=[code_snippet],
            metadatas=[metadata]
        )
        
        return pattern_id
    
    async def find_similar_patterns(
        self,
        code_query: str,
        shopware_version: Optional[str] = None,
        pattern_type: Optional[PatternType] = None,
        language: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Findet ähnliche Code-Patterns.
        
        Args:
            code_query: Code-Query oder Beschreibung
            shopware_version: Filter nach Shopware-Version
            pattern_type: Filter nach Pattern-Typ
            language: Filter nach Sprache
            limit: Anzahl Ergebnisse
            
        Returns:
            Liste ähnlicher Patterns
        """
        collection = self._get_collection(self.COLLECTION_PATTERNS)
        
        # Build filter
        where_filter = {}
        if shopware_version:
            where_filter["shopware_version"] = shopware_version
        if pattern_type:
            where_filter["pattern_type"] = pattern_type.value if isinstance(pattern_type, PatternType) else pattern_type
        if language:
            where_filter["language"] = language
        
        # Query
        results = collection.query(
            query_texts=[code_query],
            n_results=limit,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        return self._format_results(results)
    
    async def increment_pattern_success(self, pattern_id: str) -> None:
        """Erhöht Success-Rate eines Patterns."""
        collection = self._get_collection(self.COLLECTION_PATTERNS)
        
        # Get current metadata
        result = collection.get(ids=[pattern_id], include=["metadatas"])
        if result["metadatas"]:
            metadata = result["metadatas"][0]
            metadata["success_rate"] = min(1.0, metadata.get("success_rate", 0) + 0.1)
            metadata["usage_count"] = metadata.get("usage_count", 0) + 1
            metadata["updated_at"] = datetime.utcnow().isoformat()
            
            collection.update(
                ids=[pattern_id],
                metadatas=[metadata]
            )
    
    async def flag_pattern_for_review(self, pattern_id: str, ticket_id: str) -> None:
        """Markiert Pattern für Review (bei Fehlschlag)."""
        collection = self._get_collection(self.COLLECTION_PATTERNS)
        
        result = collection.get(ids=[pattern_id], include=["metadatas"])
        if result["metadatas"]:
            metadata = result["metadatas"][0]
            metadata["needs_review"] = True
            metadata["flagged_by_ticket"] = ticket_id
            metadata["success_rate"] = max(0.0, metadata.get("success_rate", 1.0) - 0.2)
            metadata["updated_at"] = datetime.utcnow().isoformat()
            
            collection.update(
                ids=[pattern_id],
                metadatas=[metadata]
            )
    
    # === Solutions ===
    
    async def store_solution(
        self,
        ticket_id: str,
        problem_description: str,
        solution_description: str,
        solution_type: SolutionType,
        code_changes: Optional[str] = None,
        affected_files: Optional[List[str]] = None,
        shopware_version: Optional[str] = None,
        plugins: Optional[List[str]] = None,
        verified: bool = False,
        resolution_time_hours: Optional[float] = None,
        agent_id: Optional[str] = None,
        solution_id: Optional[str] = None
    ) -> str:
        """Speichert eine erfolgreiche Lösung.
        
        Args:
            ticket_id: Ticket ID
            problem_description: Problembeschreibung
            solution_description: Lösungsbeschreibung
            solution_type: Art der Lösung
            code_changes: Code-Änderungen
            affected_files: Betroffene Dateien
            shopware_version: Shopware-Version
            plugins: Installierte Plugins
            verified: Ob die Lösung verifiziert wurde
            resolution_time_hours: Zeit zur Lösung
            agent_id: Agent der die Lösung erstellt hat
            solution_id: Optional custom ID
            
        Returns:
            Solution ID
        """
        collection = self._get_collection(self.COLLECTION_SOLUTIONS)
        
        if solution_id is None:
            solution_id = f"sol_{ticket_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Document: Kombination aus Problem und Lösung für bessere Suche
        document = f"""Problem: {problem_description}

Symptome: {problem_description[:200]}

Lösung: {solution_description}

Code Changes:
{code_changes or "N/A"}
"""
        
        metadata = {
            "ticket_id": ticket_id,
            "solution_type": solution_type.value if isinstance(solution_type, SolutionType) else solution_type,
            "affected_files": json.dumps(affected_files or []),
            "shopware_version": shopware_version or "",
            "plugins": json.dumps(plugins or []),
            "success_verified": verified,
            "resolution_time_hours": resolution_time_hours or 0.0,
            "created_by_agent": agent_id or "",
            "created_at": datetime.utcnow().isoformat()
        }
        
        collection.add(
            ids=[solution_id],
            documents=[document],
            metadatas=[metadata]
        )
        
        return solution_id
    
    async def find_similar_solutions(
        self,
        problem_description: str,
        shopware_version: Optional[str] = None,
        solution_type: Optional[SolutionType] = None,
        verified_only: bool = True,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Findet ähnliche, bereits gelöste Probleme.
        
        Args:
            problem_description: Aktuelles Problem
            shopware_version: Filter nach Version
            solution_type: Filter nach Lösungs-Typ
            verified_only: Nur verifizierte Lösungen
            limit: Anzahl Ergebnisse
            
        Returns:
            Liste ähnlicher Lösungen
        """
        collection = self._get_collection(self.COLLECTION_SOLUTIONS)
        
        # Build filter
        where_filter = {}
        if verified_only:
            where_filter["success_verified"] = True
        if shopware_version:
            where_filter["shopware_version"] = shopware_version
        if solution_type:
            where_filter["solution_type"] = solution_type.value if isinstance(solution_type, SolutionType) else solution_type
        
        results = collection.query(
            query_texts=[problem_description],
            n_results=limit,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        return self._format_results(results)
    
    async def verify_solution(self, solution_id: str) -> bool:
        """Markiert eine Lösung als verifiziert."""
        collection = self._get_collection(self.COLLECTION_SOLUTIONS)
        
        result = collection.get(ids=[solution_id], include=["metadatas"])
        if result["metadatas"]:
            metadata = result["metadatas"][0]
            metadata["success_verified"] = True
            metadata["verified_at"] = datetime.utcnow().isoformat()
            
            collection.update(
                ids=[solution_id],
                metadatas=[metadata]
            )
            return True
        return False
    
    # === Documentation ===
    
    async def store_documentation(
        self,
        content: str,
        doc_type: DocType,
        topic: str,
        related_files: Optional[List[str]] = None,
        verified_by: Optional[str] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """Speichert Projekt-Dokumentation.
        
        Args:
            content: Dokumentations-Inhalt
            doc_type: Art der Dokumentation
            topic: Thema/Titel
            related_files: Verwandte Dateien
            verified_by: Wer hat es verifiziert
            doc_id: Optional custom ID
            
        Returns:
            Doc ID
        """
        collection = self._get_collection(self.COLLECTION_DOCUMENTATION)
        
        if doc_id is None:
            import hashlib
            doc_id = hashlib.md5(f"{topic}:{content[:100]}".encode()).hexdigest()
        
        metadata = {
            "doc_type": doc_type.value if isinstance(doc_type, DocType) else doc_type,
            "topic": topic,
            "related_files": json.dumps(related_files or []),
            "created_at": datetime.utcnow().isoformat(),
            "last_verified": datetime.utcnow().isoformat() if verified_by else "",
            "verified_by": verified_by or ""
        }
        
        collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata]
        )
        
        return doc_id
    
    async def find_documentation(
        self,
        query: str,
        doc_type: Optional[DocType] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Findet relevante Dokumentation."""
        collection = self._get_collection(self.COLLECTION_DOCUMENTATION)
        
        where_filter = {}
        if doc_type:
            where_filter["doc_type"] = doc_type.value if isinstance(doc_type, DocType) else doc_type
        
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        return self._format_results(results)
    
    # === Conversations ===
    
    async def store_conversation_summary(
        self,
        ticket_id: str,
        summary: str,
        conversation_type: str = "ticket",  # ticket, chat, email
        participants: Optional[List[str]] = None,
        key_decisions: Optional[List[str]] = None,
        outcome: Optional[str] = None,
        summary_id: Optional[str] = None
    ) -> str:
        """Speichert Konversations-Zusammenfassung."""
        collection = self._get_collection(self.COLLECTION_CONVERSATIONS)
        
        if summary_id is None:
            summary_id = f"conv_{ticket_id}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        metadata = {
            "ticket_id": ticket_id,
            "conversation_type": conversation_type,
            "participants": json.dumps(participants or []),
            "key_decisions": json.dumps(key_decisions or []),
            "outcome": outcome or "",
            "created_at": datetime.utcnow().isoformat()
        }
        
        collection.add(
            ids=[summary_id],
            documents=[summary],
            metadatas=[metadata]
        )
        
        return summary_id
    
    async def find_conversations(
        self,
        query: str,
        conversation_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Findet ähnliche Konversationen."""
        collection = self._get_collection(self.COLLECTION_CONVERSATIONS)
        
        where_filter = {}
        if conversation_type:
            where_filter["conversation_type"] = conversation_type
        
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )
        
        return self._format_results(results)
    
    # === Utility ===
    
    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Formatiert ChromaDB-Results in einfache Liste."""
        formatted = []
        
        if not results["ids"] or not results["ids"][0]:
            return formatted
        
        for i, doc_id in enumerate(results["ids"][0]):
            item = {
                "id": doc_id,
                "content": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else None
            }
            formatted.append(item)
        
        return formatted
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über alle Collections."""
        stats = {}
        
        for coll_type in [
            self.COLLECTION_PATTERNS,
            self.COLLECTION_SOLUTIONS,
            self.COLLECTION_DOCUMENTATION,
            self.COLLECTION_CONVERSATIONS
        ]:
            try:
                collection = self._get_collection(coll_type)
                count = collection.count()
                stats[coll_type] = {"count": count}
            except Exception:
                stats[coll_type] = {"count": 0, "error": "Collection not accessible"}
        
        return {
            "customer_id": self.customer_id,
            "collections": stats
        }
    
    async def reset_customer_memory(self) -> None:
        """Löscht ALLE Langzeit-Gedächtnis-Daten für diesen Kunden."""
        for coll_type in [
            self.COLLECTION_PATTERNS,
            self.COLLECTION_SOLUTIONS,
            self.COLLECTION_DOCUMENTATION,
            self.COLLECTION_CONVERSATIONS
        ]:
            try:
                collection_name = self._get_collection_name(coll_type)
                self.client.delete_collection(collection_name)
                if coll_type in self._collections:
                    del self._collections[coll_type]
            except ValueError:
                pass  # Collection didn't exist
