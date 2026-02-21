# Mohami - Wissensbasis

## Technische Systeme

### Core Stack
- **Python 3.11** - Hauptprogrammiersprache
- **FastAPI** - Backend API Framework
- **React 18** - Frontend Framework
- **SQLite** - Datenbank (für Kanban & Tickets)
- **Redis** - Session Cache & Git Cache
- **ChromaDB** - Vektor-Datenbank für Langzeitgedächtnis

### Infrastructure
- **Docker / Docker Compose** - Container-Orchestrierung
- **GitHub API** - Repository-Zugriff, PRs, Commits
- **Bitbucket API** - Alternative Git-Provider
- **OpenRouter** - LLM-Provider (Kimi 2.5)
- **DDEV** - Lokale Entwicklungsumgebung für PHP/Shopware

### Projektstruktur
```
/home/rin/Work/personal-ki-agents/
├── src/
│   ├── kanban/           # FastAPI Backend (Tickets, Comments)
│   ├── agents/           # Agent-Implementierungen
│   ├── memory/           # Gedächtnis-Systeme (ChromaDB, Redis)
│   ├── tools/            # Tool-Registry & Tools
│   ├── git_provider/     # GitHub/Bitbucket Integration
│   ├── git_cache/        # Redis-basierter Git-Cache
│   ├── llm/              # KimiClient für LLM-Zugriff
│   ├── agent_config/     # Config-Loader für Agents
│   └── infrastructure/   # DDEV, Workspace Manager
├── agents/               # Agent-Konfigurationen
│   ├── mohami/          # Dieser Agent
│   └── TEMPLATE/        # Template für neue Agents
├── frontend/            # React Frontend
├── pm/                  # Projekt-Management Dokumente
├── agent_worker.py      # Haupt-Worker-Prozess
└── docker-compose.yml   # Docker-Setup
```

## Entwicklungs-Workflow

### 1. Ticket aus Kanban lesen
- Worker prüft alle 5 Sekunden auf neue Tickets
- Status: backlog → in_progress
- Agent wird zugewiesen

### 2. Repository analysieren
- GitHub/Bitbucket API für Repo-Info
- Git Cache (Redis) für Dateiliste
- Prüfen ob Repository leer ist

### 3. ORPA-Workflow ausführen
```
OBSERVE → REASON → PLAN → ACT
```

**OBSERVE:**
- Ticket-Details laden
- Customer Context laden (aus memories/)
- Repository-Snapshot laden
- Episodic Memory abfragen (ähnliche Tickets)

**REASON:**
- LLM-Analyse mit vollem Kontext
- System-Prompt enthält:
  - Agent Personality (soul.md)
  - Rules (rules.md)
  - Customer Context
  - Episodic Memories
  - Repository Status

**PLAN:**
- Implementierungsplan erstellen
- Tools identifizieren die benötigt werden
- Rückfragen stellen wenn unklar

**ACT:**
- Tools ausführen (File Tools, Git Tools, Code Tools, DDEV Tools)
- Änderungen committen
- PR erstellen oder Initial-Commit

### 4. Memory aktualisieren
- Episodic Memory: Ticket-Ablauf speichern
- Lessons Learned: Erfolgreiche Lösungen
- Git Cache: Repository-Status aktualisieren

## Wichtige Links

### Projekt-Dokumentation
- `/pm/Architektur-Projektplan.md` - Gesamtarchitektur
- `/pm/memory-context-management-plan.md` - Gedächtnis-System
- `/pm/MVP-Plan-GitHub.md` - GitHub Integration
- `/pm/PM-Tool-Integration-Plan.md` - Kanban/PM Integration
- `/pm/Security-und-MVP-Plan.md` - Security & MVP
- `/pm/Projektplan-KI-Mitarbeiter.md` - Gesamtprojekt

### Code-Referenz
- `src/agents/enhanced_agent.py` - Haupt-Agent-Logik (ORPA)
- `src/tools/` - Tool-System
- `src/memory/` - Gedächtnis-Implementierung
- `src/git_provider/` - Git-Integration

### API Endpunkte
| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | /tickets | Alle Tickets |
| POST | /tickets | Ticket erstellen |
| GET | /tickets/{id} | Ticket Details |
| POST | /tickets/{id}/comments | Kommentar hinzufügen |
| GET | /queue/{agent_id} | Agent Queue |

## Environment Variablen

```bash
# API Keys
OPEN_ROUTER_API_KEY=sk-or-...
GITHUB_TOKEN=ghp_...
KIMI_API_KEY=...

# Database
DATABASE_URL=sqlite:///./kanban.db
REDIS_URL=redis://localhost:6379
CHROMA_PERSIST_DIR=./data/chroma

# Features
USE_ENHANCED_AGENT=true  # Aktiviert volles Gedächtnis
```

## Agenten-Konfiguration

### Config-Loading
```python
from src.agent_config import AgentConfigLoader

loader = AgentConfigLoader("./agents/mohami")
config = loader.load_config("mohami")
# Lädt: soul.md, rules.md, knowledge.md, memories/
```

### Memory-System
```python
# Kurzzeit (In-Memory)
context.current_ticket

# Sitzung (Redis)
redis.get(f"customer:{customer_id}:session:{session_id}:context")

# Langzeit (ChromaDB)
memory_store.query(
    collection=f"customer_{customer_id}_patterns",
    query_text="..."
)

# Episodisch (PostgreSQL + Vektoren)
episodic_memory.record_ticket_resolution(...)
```

## Troubleshooting

### Agent startet nicht
```bash
# Prüfe API Keys
python -c "import os; print('OK' if os.getenv('OPEN_ROUTER_API_KEY') else 'MISSING')"
```

### Frontend kann nicht auf API zugreifen
```bash
# Proxy-Einstellung prüfen (frontend/package.json)
# Oder REACT_APP_API_URL setzen
```

### Memory-System nicht verfügbar
- Prüfe Redis: `redis-cli ping`
- Prüfe ChromaDB: `ls -la ./data/chroma/`
- Enhanced Agent deaktiviert sich automatisch bei Fehlern

### GitHub API Rate Limits
- Git Cache (Redis) reduziert API-Calls
- Bei 403: Token prüfen oder Rate-Limit abwarten
