# Memory-System

## Übersicht
Das 4-Schichten Gedächtnis-System für Multi-Agent-Entwicklung mit Kunden-Isolation.

## Architektur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         4-SCHICHTEN GEDÄCHTNIS-MODELL                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  SCHICHT 1      │  │  SCHICHT 2      │  │  SCHICHT 3      │             │
│  │  KURZZEIT       │  │  SITZUNG        │  │  LANGZEIT       │             │
│  │  (In-Memory)    │  │  (Redis)        │  │  (ChromaDB)     │             │
│  │  Millisekunden  │  │  24-48h TTL     │  │  Permanent      │             │
│  │                 │  │                 │  │                 │             │
│  │  • Aktiver      │  │  • Chat-Verlauf │  │  • Code-Patterns│             │
│  │    Kontext      │  │  • Temp. Daten  │  │  • Lösungen     │             │
│  │  • Reasoning    │  │  • Zwischen-    │  │  • Wissen       │             │
│  │    Zwischen-    │  │    ergebnisse   │  │  • Embeddings   │             │
│  │    schritte     │  │                 │  │                 │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           └────────────────────┴────────────────────┘                       │
│                              │                                              │
│           ┌──────────────────┴──────────────────┐                          │
│           │  SCHICHT 4: EPISODISCHES GEDÄCHTNIS │                          │
│           │  (PostgreSQL + Vektor-Erweiterung)   │                          │
│           │                                      │                          │
│           │  • Ticket-Historie (vollständig)     │                          │
│           │  • Fehler-Ereignisse mit Kontext     │                          │
│           │  • Kunden-spezifische Workflows      │                          │
│           │  • Zeitliche Abfolge & Kausalität    │                          │
│           └─────────────────────────────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Kunden-Isolation

Jeder Kunde hat isolierte Namespaces:

| Schicht | Isolation-Mechanismus | Beispiel-Key |
|---------|----------------------|--------------|
| Kurzzeit | Objekt-Attribut | `memory.customer_id = "alp-shopware"` |
| Sitzung | Redis Key-Prefix | `sess:{customer_id}:{session_id}:...` |
| Langzeit | ChromaDB Collection | `collection = "customer_{customer_id}"` |
| Episodisch | PostgreSQL Schema | `schema = "customer_{customer_id}"` |

## Implementierungen

### Schicht 1: Kurzzeit (`src/memory/short_term.py`)
```python
from src.memory import ShortTermMemory

memory = ShortTermMemory()
memory.set_context("current_ticket", ticket_id, customer_id)
context = memory.get_context(customer_id)
```

### Schicht 2: Sitzung (`src/memory/session_redis.py`)
```python
from src.memory import SessionMemory

session = SessionMemory(redis_client, customer_id, session_id)
await session.add_message({"role": "user", "content": "..."})
history = await session.get_chat_history()
```

### Schicht 3: Langzeit (`src/memory/chroma_store.py`)
```python
from src.memory import ChromaMemoryStore

store = ChromaMemoryStore(persist_dir="./data/chroma")

# Code-Patterns speichern
store.add_to_collection(
    collection_name=f"customer_{customer_id}_patterns",
    documents=[code_snippet],
    metadatas=[{"file_path": "...", "success_rate": 0.95}]
)

# Ähnliche Patterns finden
results = store.query(
    collection_name=f"customer_{customer_id}_patterns",
    query_text="repository decorator pattern",
    n_results=5
)
```

### Schicht 4: Episodisch (`src/memory/episodic_memory.py`)
```python
from src.memory import EpisodicMemory

episodic = EpisodicMemory(memory_store, embedding_provider)

# Konversation speichern
await episodic.record_conversation_turn(
    customer_id=customer_id,
    ticket_id=ticket_id,
    author="mohami",
    content="..."
)

# Ähnliche Episoden finden
context = await episodic.get_relevant_context(
    customer_id=customer_id,
    current_ticket_description="...",
    n_lessons=2,
    n_episodes=2
)
```

## Kontext-Layer Hierarchie

```
Level 1: KUNDE (Customer)
  ├── Kunden-ID: alp-shopware
  ├── Unternehmensdaten
  ├── Kontaktpersonen
  └── Historische Lern-Muster

Level 2: PROJEKT (Project)
  ├── Projekt-ID: alp-shopware-prod
  ├── Projekt-Typ: Production / Staging / Dev
  └── Verantwortliche Agents

Level 3: REPOSITORY (Repository)
  ├── Repo-URL: github.com/netgrade/alp-shopware
  ├── Primär-Sprache: PHP
  └── Branch-Strategie: GitFlow

Level 4: TECH-STACK (TechStack)
  ├── Shopware-Version: 6.5.8.14
  ├── PHP-Version: 8.1
  ├── Datenbank: MariaDB 10.4
  └── Cache: Redis

Level 5: PLUGINS & ERWEITERUNGEN
  ├── Core-Plugins (Shopware)
  ├── Netgrade-Plugins (eigene)
  └── Third-Party Plugins

Level 6: AKTUELLER KONTEXT (CurrentContext)
  ├── Aktives Ticket/Issue
  ├── Aktuelle Dateien (geöffnet)
  └── Konversations-Verlauf
```

## Redis Key-Struktur

```
# Session
customer:{customer_id}:session:{session_id}:meta
customer:{customer_id}:session:{session_id}:context

# Chat History
customer:{customer_id}:chat:{chat_id}:messages
customer:{customer_id}:chat:{chat_id}:summary

# Cache
customer:{customer_id}:cache:tech_stack
customer:{customer_id}:cache:plugins
customer:{customer_id}:cache:git:{cache_key}

# ORPA-Zustand
customer:{customer_id}:orpa:{session_id}:current_phase
customer:{customer_id}:orpa:{session_id}:plan

# Locks
customer:{customer_id}:lock:ticket:{ticket_id}
customer:{customer_id}:lock:file:{file_path_hash}
```

## Nutzung im Agenten

```python
class EnhancedDeveloperAgent:
    def __init__(self, ...):
        self.context_manager = CustomerContextManager(
            agent_id=agent_id,
            memory_store=memory_store,
            embedding_provider=embeddings
        )
        self.episodic_memory = EpisodicMemory(
            memory_store=memory_store,
            embedding_provider=embeddings
        )
        self.git_cache = GitRepoCache(git_provider, redis_url)

    async def process_ticket(self, ticket_id):
        # 1. Kurzzeit: Ticket laden
        ticket = await self.tickets.get(ticket_id)
        
        # 2. Sitzung: Chat-Verlauf laden
        comments = await self.comments.get_by_ticket(ticket_id)
        
        # 3. Langzeit: Customer Context laden
        context = await self.context_manager.get_context_summary(ticket.customer)
        
        # 4. Episodisch: Ähnliche Tickets finden
        episodic = await self.episodic_memory.get_relevant_context(
            customer_id=ticket.customer,
            current_ticket_description=ticket.description
        )
        
        # Git Cache: Repository-Status
        repo = await self.git_cache.refresh_if_needed(ticket.repository)
```

## Lern-Algorithmus

```python
class ContinuousLearningEngine:
    def process_ticket_resolution(self, ticket, outcome):
        if outcome.status == "success":
            # Als erfolgreiche Lösung speichern
            self.solution_memory.store_solution(ticket, outcome)
            # Success-Rate aktualisieren
            for pattern in outcome.used_patterns:
                self.pattern_memory.increment_success(pattern.id)
        elif outcome.status == "failure":
            # Fehler-Episode speichern
            self.error_memory.store_episode(ticket, outcome)
```
