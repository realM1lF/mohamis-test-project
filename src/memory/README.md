# 4-Schichten Gedächtnis-System

Das Gedächtnis-System für Mohami ist in 4 Schichten organisiert, von flüchtig zu persistent.

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED MEMORY MANAGER                        │
│              (UnifiedMemoryManager - unified_manager.py)         │
└──────────┬──────────────────────────────────────────────────────┘
           │
    ┌──────┴──────┬──────────────┬──────────────┬────────────────┐
    │             │              │              │                │
    ▼             ▼              ▼              ▼                ▼
┌────────┐  ┌──────────┐  ┌────────────┐  ┌───────────┐    ┌──────────┐
│Short   │  │ Session  │  │ Long Term  │  │ Episodic  │    │  External│
│Term    │  │ (Redis)  │  │ (ChromaDB) │  │ (SQLite)  │    │  (PG)    │
├────────┤  ├──────────┤  ├────────────┤  ├───────────┤    ├──────────┤
│InMemory│  │ Chat     │  │ Code       │  │ Ticket    │    │ (Future) │
│Buffer  │  │ History  │  │ Patterns   │  │ Resolution│    │          │
│        │  │ Session  │  │ Solutions  │  │ Lessons   │    │          │
│        │  │ State    │  │ Embeddings │  │ History   │    │          │
├────────┤  ├──────────┤  ├────────────┤  ├───────────┤    ├──────────┤
│~1h TTL │  │~24h TTL  │  │ Permanent  │  │ Permanent │    │ Permanent│
└────────┘  └──────────┘  └────────────┘  └───────────┘    └──────────┘
```

## Schichten

### 1. Short Term (InMemoryBuffer)
**Datei:** `short_term.py`

- **Speicherort:** RAM (In-Memory)
- **Lebensdauer:** ~1 Stunde (TTL-basiert)
- **Verwendung:** Aktive Session-Daten, ORPA-Loop State, Reasoning-Schritte
- **API:**
  ```python
  buffer = InMemoryBuffer(customer_id="customer-1")
  buffer.set("key", value, ttl=3600)
  value = buffer.get("key")
  ```

### 2. Session (RedisMemory)
**Datei:** `session_redis.py`

- **Speicherort:** Redis
- **Lebensdauer:** 24-48 Stunden
- **Verwendung:** Chat-History, Session-State, temporäre Daten
- **API:**
  ```python
  memory = RedisMemory(customer_id="customer-1", redis_client=redis)
  memory.add_chat_message(ticket_id, {"role": "user", "content": "..."})
  history = memory.get_chat_history(ticket_id)
  ```

### 3. Long Term (ChromaLongTermMemory)
**Datei:** `long_term_chroma.py`

- **Speicherort:** ChromaDB (lokale Dateien)
- **Lebensdauer:** Permanent
- **Verwendung:** Code-Patterns, Lösungen, Embeddings für semantische Suche
- **API:**
  ```python
  memory = ChromaLongTermMemory(customer_id, chroma_client)
  memory.store_code_pattern(pattern, metadata)
  results = memory.find_similar_patterns(query)
  ```

### 4. Episodic (EpisodicMemory)
**Datei:** `episodic_db.py`

- **Speicherort:** SQLite (später PostgreSQL)
- **Lebensdauer:** Permanent
- **Verwendung:** Ticket-Resolutionen, Lessons Learned, Konversations-Verlauf
- **API:**
  ```python
  memory = EpisodicMemory(customer_id, db_path)
  memory.record_ticket_resolution(ticket_id, problem, solution, success)
  episodes = memory.get_relevant_episodes(query)
  ```

## Unified Memory Manager

**Datei:** `unified_manager.py`

Verbindet alle 4 Schichten und bietet eine einheitliche API:

```python
from memory import UnifiedMemoryManager, LearningEpisode

# Initialisieren
manager = UnifiedMemoryManager(customer_id="customer-1")

# Kontext speichern (auto-tier)
manager.store_context("current_ticket", ticket_data)

# Kontext abrufen
value = manager.retrieve_context("current_ticket")

# Learning aufzeichnen
episode = LearningEpisode(
    ticket_id="TICKET-123",
    problem="Payment error",
    solution="Fixed validation",
    success=True
)
manager.record_learning(episode)

# Agent-Kontext bauen
context = manager.build_agent_context(ticket_id="TICKET-123")
```

### Auto-Tier Zuweisung

Basierend auf Key-Prefix wird automatisch die passende Schicht gewählt:

| Prefix | Schicht |
|--------|---------|
| `ticket_` | Session (Redis) |
| `chat_` | Session (Redis) |
| `pattern_` | Long Term (Chroma) |
| `solution_` | Long Term (Chroma) |
| `lesson_` | Episodic (SQLite) |
| `temp_` | Short Term (InMemory) |
| `current_` | Short Term (InMemory) |

## Installation

```bash
# Basis (nur Short Term + Episodic)
pip install -r requirements.txt

# Mit Redis
pip install redis

# Mit ChromaDB
pip install chromadb
```

## Tests

```bash
cd src/memory
python test_memory_system.py
```

## Verzeichnisstruktur

```
src/memory/
├── __init__.py              # Public API
├── short_term.py            # Schicht 1: InMemoryBuffer
├── session_redis.py         # Schicht 2: RedisMemory
├── long_term_chroma.py      # Schicht 3: ChromaLongTermMemory
├── episodic_db.py           # Schicht 4: EpisodicMemory
├── unified_manager.py       # UnifiedMemoryManager
├── chroma_store.py          # Bestehende ChromaDB Integration
├── embeddings.py            # Embedding Provider
├── context_manager.py       # Bestehender Context Manager
├── episodic/                # SQLAlchemy Models (für PostgreSQL)
│   ├── models.py
│   └── database.py
├── test_memory_system.py    # Tests
└── README.md                # Diese Datei
```

## Migration PostgreSQL (Future)

Für Episodic Memory ist ein Migrationspfad zu PostgreSQL vorbereitet:

```python
# Statt:
from memory import EpisodicMemory
memory = EpisodicMemory(customer_id, db_path)

# Später:
from memory.episodic import AsyncEpisodicMemory
memory = AsyncEpisodicMemory(customer_id, pg_connection)
```

Die SQLAlchemy Models in `episodic/models.py` sind bereits für PostgreSQL vorbereitet.
