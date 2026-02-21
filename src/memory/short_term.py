"""Schicht 1: Short Term Memory (In-Memory Buffer).

Diese Schicht speichert:
- Aktueller Kontext während einer Session
- Reasoning-Schritte und Zwischenergebnisse
- Temporäre Variablen und Tool-State

Lebensdauer: Millisekunden bis Sekunden (Session-Dauer)
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import copy
import threading


@dataclass
class ReasoningStep:
    """Ein einzelner Reasoning-Schritt während der Verarbeitung."""
    step_number: int
    phase: str  # "observe", "reason", "plan", "act"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Entry with TTL support."""
    value: Any
    expires_at: Optional[datetime] = None


class InMemoryBuffer:
    """In-Memory Buffer für Kurzzeit-Gedächtnis.
    
    Dict-basiert, pro Customer isoliert.
    Thread-sicher durch Locking.
    
    Usage:
        buffer = InMemoryBuffer(customer_id="alp-shopware")
        buffer.set("current_ticket", ticket_data, ttl=3600)
        value = buffer.get("current_ticket")
    """
    
    def __init__(self, customer_id: str, max_reasoning_steps: int = 100):
        """Initialize short-term memory buffer.
        
        Args:
            customer_id: Customer identifier for isolation
            max_reasoning_steps: Maximum reasoning steps to keep (FIFO)
        """
        self.customer_id = customer_id
        self._lock = threading.RLock()
        
        # Haupt-Daten-Store mit TTL
        self._data: Dict[str, CacheEntry] = {}
        
        # Reasoning-Schritte (begrenzte Queue)
        self._reasoning_steps: deque = deque(maxlen=max_reasoning_steps)
        
        # Aktiver Kontext (schneller Zugriff)
        self._context: Dict[str, Any] = {
            "customer_id": customer_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
        }
        
        # Tool-State (für aktive Tool-Execution)
        self._tool_state: Dict[str, Any] = {}
        
        # ORPA Loop State
        self._orpa_state: Dict[str, Any] = {
            "current_phase": None,  # observe, reason, plan, act
            "observations": [],
            "reasoning_output": None,
            "current_plan": [],
            "execution_results": []
        }
    
    # === Grundlegende Get/Set Operationen ===
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Speichert einen Wert im Buffer.
        
        Args:
            key: Schlüssel für den Wert
            value: Der zu speichernde Wert
            ttl: Time-to-live in Sekunden (default: 3600 = 1 Stunde)
        """
        with self._lock:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
            self._data[key] = CacheEntry(value=value, expires_at=expires_at)
            self._update_access_time()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Liest einen Wert aus dem Buffer.
        
        Args:
            key: Schlüssel des Werts
            default: Default-Wert wenn Key nicht existiert oder abgelaufen
            
        Returns:
            Der gespeicherte Wert oder default
        """
        with self._lock:
            self._update_access_time()
            entry = self._data.get(key)
            
            if entry is None:
                return default
            
            # Prüfe ob abgelaufen
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                del self._data[key]
                return default
            
            return entry.value
    
    def has(self, key: str) -> bool:
        """Prüft ob ein Key existiert (und nicht abgelaufen ist)."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return False
            if entry.expires_at and datetime.utcnow() > entry.expires_at:
                del self._data[key]
                return False
            return True
    
    def delete(self, key: str) -> bool:
        """Löscht einen Key. Returns True if existed."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def clear(self) -> None:
        """Löscht alle Daten (außer Session-Info)."""
        with self._lock:
            self._data.clear()
            self._reasoning_steps.clear()
            self._tool_state.clear()
            self._orpa_state = {
                "current_phase": None,
                "observations": [],
                "reasoning_output": None,
                "current_plan": [],
                "execution_results": []
            }
    
    def get_all(self) -> Dict[str, Any]:
        """Gibt komplette Daten-Kopie zurück (nur nicht abgelaufene)."""
        with self._lock:
            result = {}
            now = datetime.utcnow()
            for key, entry in list(self._data.items()):
                if entry.expires_at and now > entry.expires_at:
                    del self._data[key]
                else:
                    result[key] = copy.deepcopy(entry.value)
            return result
    
    # === Cleanup ===
    
    def cleanup_expired(self) -> int:
        """Entfernt abgelaufene Einträge. Returns Anzahl gelöschter."""
        with self._lock:
            now = datetime.utcnow()
            expired = [
                key for key, entry in self._data.items()
                if entry.expires_at and now > entry.expires_at
            ]
            for key in expired:
                del self._data[key]
            return len(expired)
    
    # === Reasoning-Schritte ===
    
    def add_reasoning_step(self, phase: str, content: str, metadata: Dict = None) -> ReasoningStep:
        """Fügt einen Reasoning-Schritt hinzu.
        
        Args:
            phase: ORPA-Phase (observe, reason, plan, act)
            content: Beschreibung des Schritts
            metadata: Zusätzliche Metadaten
            
        Returns:
            Der erstellte ReasoningStep
        """
        with self._lock:
            step = ReasoningStep(
                step_number=len(self._reasoning_steps) + 1,
                phase=phase,
                content=content,
                metadata=metadata or {}
            )
            self._reasoning_steps.append(step)
            self._update_access_time()
            return step
    
    def get_reasoning_steps(self, phase: Optional[str] = None, limit: int = None) -> List[ReasoningStep]:
        """Gibt Reasoning-Schritte zurück.
        
        Args:
            phase: Optional Filter nach Phase
            limit: Maximum Anzahl (neueste zuerst)
        """
        with self._lock:
            steps = list(self._reasoning_steps)
            
            if phase:
                steps = [s for s in steps if s.phase == phase]
            
            if limit:
                steps = steps[-limit:]
                
            return steps
    
    def get_reasoning_trace(self) -> str:
        """Gibt formatierten Reasoning-Trace zurück."""
        with self._lock:
            lines = ["=== Reasoning Trace ==="]
            for step in self._reasoning_steps:
                lines.append(f"[{step.step_number}] {step.phase.upper()}: {step.content}")
            return "\n".join(lines)
    
    def clear_reasoning(self) -> None:
        """Löscht alle Reasoning-Schritte."""
        with self._lock:
            self._reasoning_steps.clear()
    
    # === ORPA Loop State ===
    
    def set_orpa_phase(self, phase: str) -> None:
        """Setzt die aktuelle ORPA-Phase."""
        with self._lock:
            self._orpa_state["current_phase"] = phase
            self._update_access_time()
    
    def get_orpa_phase(self) -> Optional[str]:
        """Gibt aktuelle ORPA-Phase zurück."""
        with self._lock:
            return self._orpa_state["current_phase"]
    
    def add_observation(self, observation: str, metadata: Dict = None) -> None:
        """Fügt eine Beobachtung hinzu (Observe-Phase)."""
        with self._lock:
            self._orpa_state["observations"].append({
                "content": observation,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            })
            self._update_access_time()
    
    def get_observations(self) -> List[Dict]:
        """Gibt alle gesammelten Beobachtungen zurück."""
        with self._lock:
            return copy.deepcopy(self._orpa_state["observations"])
    
    def set_reasoning_output(self, output: str) -> None:
        """Setzt Reasoning-Output (Reason-Phase)."""
        with self._lock:
            self._orpa_state["reasoning_output"] = output
            self._update_access_time()
    
    def get_reasoning_output(self) -> Optional[str]:
        """Gibt Reasoning-Output zurück."""
        with self._lock:
            return self._orpa_state["reasoning_output"]
    
    def set_plan(self, steps: List[Dict]) -> None:
        """Setzt den aktuellen Plan (Plan-Phase)."""
        with self._lock:
            self._orpa_state["current_plan"] = steps
            self._update_access_time()
    
    def get_plan(self) -> List[Dict]:
        """Gibt aktuellen Plan zurück."""
        with self._lock:
            return copy.deepcopy(self._orpa_state["current_plan"])
    
    def add_execution_result(self, step_id: str, result: Any, success: bool = True) -> None:
        """Fügt ein Execution-Result hinzu (Act-Phase)."""
        with self._lock:
            self._orpa_state["execution_results"].append({
                "step_id": step_id,
                "result": result,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            })
            self._update_access_time()
    
    def get_execution_results(self) -> List[Dict]:
        """Gibt alle Execution-Results zurück."""
        with self._lock:
            return copy.deepcopy(self._orpa_state["execution_results"])
    
    # === Tool State ===
    
    def set_tool_state(self, tool_name: str, state: Dict[str, Any]) -> None:
        """Speichert State für ein aktives Tool."""
        with self._lock:
            self._tool_state[tool_name] = {
                "state": state,
                "updated_at": datetime.utcnow().isoformat()
            }
    
    def get_tool_state(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Gibt State für ein Tool zurück."""
        with self._lock:
            tool_data = self._tool_state.get(tool_name)
            return tool_data["state"] if tool_data else None
    
    def clear_tool_state(self, tool_name: str = None) -> None:
        """Löscht Tool-State (oder alle wenn kein Name angegeben)."""
        with self._lock:
            if tool_name:
                self._tool_state.pop(tool_name, None)
            else:
                self._tool_state.clear()
    
    # === Session Info ===
    
    def get_session_info(self) -> Dict[str, Any]:
        """Gibt Session-Informationen zurück."""
        with self._lock:
            self.cleanup_expired()
            return {
                "customer_id": self.customer_id,
                "created_at": self._context["created_at"],
                "last_accessed": self._context["last_accessed"],
                "data_keys": list(self._data.keys()),
                "data_count": len(self._data),
                "reasoning_steps_count": len(self._reasoning_steps),
                "current_orpa_phase": self._orpa_state["current_phase"]
            }
    
    # === Private Helpers ===
    
    def _update_access_time(self) -> None:
        """Aktualisiert last_accessed Timestamp."""
        self._context["last_accessed"] = datetime.utcnow().isoformat()
    
    def __repr__(self) -> str:
        return f"InMemoryBuffer(customer={self.customer_id}, items={len(self._data)})"
