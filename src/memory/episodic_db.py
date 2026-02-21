"""Schicht 4: Episodic Memory (SQLite).

Diese Schicht speichert:
- Ticket-Resolutionen und Ergebnisse
- Erfolgreiche/fehlgeschlagene Ansätze
- Zeitliche Abfolge von Ereignissen

Lebensdauer: Permanent (mit Retention-Policy)
Datenbank: SQLite (für jetzt), später PostgreSQL
"""

import sqlite3
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from contextlib import contextmanager
import os


@dataclass
class TicketResolution:
    """Eine Ticket-Resolution Episode."""
    ticket_id: str
    problem: str
    solution: str
    success: bool
    timestamp: str
    metadata: Dict[str, Any]


class EpisodicMemory:
    """Episodisches Gedächtnis für Ticket-History.
    
    SQLite-basiert, pro Customer separate DB-Datei.
    Speichert Resolutionen und lernt aus vergangenen Tickets.
    
    Usage:
        memory = EpisodicMemory(
            customer_id="alp-shopware",
            db_path="./data/episodic/alp-shopware.db"
        )
        
        # Resolution aufzeichnen
        memory.record_ticket_resolution(
            ticket_id="TICKET-123",
            problem="Checkout error",
            solution="Fixed payment validation",
            success=True
        )
        
        # Ähnliche Episoden finden
        episodes = memory.get_relevant_episodes("checkout payment error")
    """
    
    def __init__(self, customer_id: str, db_path: str):
        """Initialize Episodic Memory.
        
        Args:
            customer_id: Customer identifier
            db_path: Pfad zur SQLite Datenbank
        """
        self.customer_id = customer_id
        self.db_path = db_path
        
        # Stelle sicher dass Verzeichnis existiert
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialisiere Schema
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """Context manager für DB-Connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialisiert das Datenbank-Schema."""
        with self._get_connection() as conn:
            # Episodes Tabelle
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    episode_type TEXT NOT NULL DEFAULT 'resolution',
                    ticket_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    problem_summary TEXT,
                    solution_summary TEXT,
                    success BOOLEAN,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    importance_score REAL DEFAULT 0.5,
                    search_hash TEXT
                )
            """)
            
            # Indizes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodes_ticket 
                ON episodes(ticket_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodes_type 
                ON episodes(episode_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodes_timestamp 
                ON episodes(timestamp DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodes_success 
                ON episodes(success)
            """)
            
            # Conversations Tabelle (für Chat-History)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL,
                    message_role TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_ticket 
                ON conversations(ticket_id)
            """)
            
            conn.commit()
    
    def _generate_search_hash(self, text: str) -> str:
        """Generiert einen einfachen Such-Hash aus Text."""
        # Normalisiere: lowercase, nur alphanumerisch
        normalized = ''.join(c.lower() for c in text if c.isalnum() or c.isspace())
        words = sorted(set(normalized.split()))
        return hashlib.md5(' '.join(words).encode()).hexdigest()[:16]
    
    # === Ticket Resolutions ===
    
    def record_ticket_resolution(
        self,
        ticket_id: str,
        problem: str,
        solution: str,
        success: bool,
        metadata: Dict = None
    ) -> int:
        """Zeichnet eine Ticket-Resolution auf.
        
        Args:
            ticket_id: Ticket identifier
            problem: Problembeschreibung
            solution: Die Lösung
            success: War die Lösung erfolgreich?
            metadata: Zusätzliche Metadaten
            
        Returns:
            Episode ID
        """
        content = f"## Problem\n{problem}\n\n## Solution\n{solution}"
        timestamp = datetime.utcnow().isoformat()
        search_hash = self._generate_search_hash(problem + " " + solution)
        
        # Berechne Importance-Score (erfolgreiche Lösungen sind wichtiger)
        importance = 0.8 if success else 0.4
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO episodes 
                (episode_type, ticket_id, content, problem_summary, solution_summary, 
                 success, timestamp, metadata, importance_score, search_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "resolution",
                    ticket_id,
                    content,
                    problem[:200],
                    solution[:200],
                    success,
                    timestamp,
                    json.dumps(metadata or {}),
                    importance,
                    search_hash
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_ticket_resolution(self, ticket_id: str) -> Optional[Dict]:
        """Holt die Resolution für ein spezifisches Ticket.
        
        Returns:
            Episode dict oder None
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM episodes WHERE ticket_id = ? AND episode_type = 'resolution'",
                (ticket_id,)
            ).fetchone()
            
            if row:
                return self._row_to_dict(row)
            return None
    
    # === Suche ===
    
    def get_relevant_episodes(
        self,
        query: str,
        n_results: int = 3,
        only_successful: bool = False
    ) -> List[Dict]:
        """Findet relevante Episoden basierend auf Query.
        
        Einfache Keyword-basierte Suche (keine Embeddings).
        Später erweiterbar zu semantic search.
        
        Args:
            query: Suchquery
            n_results: Anzahl der Ergebnisse
            only_successful: Nur erfolgreiche Resolutionen
            
        Returns:
            List von Episoden
        """
        query_hash = self._generate_search_hash(query)
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        
        with self._get_connection() as conn:
            # Basis query
            sql = """
                SELECT * FROM episodes 
                WHERE episode_type = 'resolution'
            """
            params = []
            
            if only_successful:
                sql += " AND success = 1"
            
            # Order by importance and recency
            sql += " ORDER BY importance_score DESC, timestamp DESC LIMIT ?"
            params.append(n_results * 3)  # Hol mehr für Keyword-Filterung
            
            rows = conn.execute(sql, params).fetchall()
            
            # Simple Keyword-Matching
            scored_results = []
            for row in rows:
                score = 0
                content = (row['content'] or '').lower()
                problem = (row['problem_summary'] or '').lower()
                
                for term in query_terms:
                    if term in problem:
                        score += 3  # Problem-Match ist wichtiger
                    if term in content:
                        score += 1
                
                if score > 0 or not query_terms:
                    scored_results.append((score, row))
            
            # Sortiere nach Score, dann nach Importance
            scored_results.sort(key=lambda x: (x[0], x[1]['importance_score']), reverse=True)
            
            # Nimm top n_results
            return [self._row_to_dict(row) for _, row in scored_results[:n_results]]
    
    def get_similar_problems(
        self,
        problem: str,
        n_results: int = 3
    ) -> List[Dict]:
        """Findet ähnliche Probleme aus der Vergangenheit.
        
        Args:
            problem: Problembeschreibung
            n_results: Anzahl der Ergebnisse
            
        Returns:
            List von Episoden mit ähnlichen Problemen
        """
        return self.get_relevant_episodes(problem, n_results, only_successful=True)
    
    # === Conversations ===
    
    def add_conversation_message(
        self,
        ticket_id: str,
        role: str,
        content: str,
        metadata: Dict = None
    ) -> int:
        """Fügt eine Konversationsnachricht hinzu.
        
        Args:
            ticket_id: Ticket identifier
            role: Rolle (user, assistant, system)
            content: Nachrichteninhalt
            metadata: Zusätzliche Metadaten
            
        Returns:
            Message ID
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO conversations 
                (ticket_id, message_role, message_content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    role,
                    content,
                    datetime.utcnow().isoformat(),
                    json.dumps(metadata or {})
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_conversation_history(
        self,
        ticket_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Holt Konversations-History für ein Ticket.
        
        Returns:
            List von Messages
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM conversations 
                WHERE ticket_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (ticket_id, limit)
            ).fetchall()
            
            return [
                {
                    "id": row['id'],
                    "ticket_id": row['ticket_id'],
                    "role": row['message_role'],
                    "content": row['message_content'],
                    "timestamp": row['timestamp'],
                    "metadata": json.loads(row['metadata']) if row['metadata'] else {}
                }
                for row in rows
            ]
    
    # === Stats ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über Episoden zurück."""
        with self._get_connection() as conn:
            # Gesamtzahl Episoden
            row = conn.execute(
                "SELECT COUNT(*) as count FROM episodes"
            ).fetchone()
            total_episodes = row['count']
            
            # Erfolgreiche Resolutionen
            row = conn.execute(
                "SELECT COUNT(*) as count FROM episodes WHERE success = 1"
            ).fetchone()
            successful = row['count']
            
            # Konversationen
            row = conn.execute(
                "SELECT COUNT(*) as count FROM conversations"
            ).fetchone()
            total_messages = row['count']
            
            # Tickets mit Resolutionen
            row = conn.execute(
                "SELECT COUNT(DISTINCT ticket_id) as count FROM episodes"
            ).fetchone()
            tickets_with_resolutions = row['count']
            
            return {
                "customer_id": self.customer_id,
                "total_episodes": total_episodes,
                "successful_resolutions": successful,
                "failed_resolutions": total_episodes - successful,
                "success_rate": successful / total_episodes if total_episodes > 0 else 0,
                "total_conversation_messages": total_messages,
                "tickets_with_resolutions": tickets_with_resolutions
            }
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Konvertiert DB-Row zu Dict."""
        return {
            "id": row['id'],
            "episode_type": row['episode_type'],
            "ticket_id": row['ticket_id'],
            "content": row['content'],
            "problem_summary": row['problem_summary'],
            "solution_summary": row['solution_summary'],
            "success": bool(row['success']),
            "timestamp": row['timestamp'],
            "metadata": json.loads(row['metadata']) if row['metadata'] else {},
            "importance_score": row['importance_score']
        }
    
    def clear_all(self) -> int:
        """Löscht alle Daten (Vorsicht!).
        
        Returns:
            Anzahl gelöschter Episoden
        """
        with self._get_connection() as conn:
            conn.execute("DELETE FROM episodes")
            conn.execute("DELETE FROM conversations")
            conn.commit()
            return conn.total_changes
    
    def __repr__(self) -> str:
        return f"EpisodicMemory(customer={self.customer_id}, db={self.db_path})"
