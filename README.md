# 🤖 KI-Mitarbeiter System

Ein Multi-Agent System für Softwareentwicklung mit:
- 🎫 Kanban Board für Ticket-Management
- 🧠 Kimi 2.5 LLM für intelligente Verarbeitung
- 🔗 GitHub Integration für Code-Änderungen
- 🔄 ORPA-Workflow (Observe-Reason-Plan-Act)

## Schnellstart

### 1. Voraussetzungen

```bash
# API Keys in .env eintragen
cp .env.example .env
# Dann editieren:
# - OPEN_ROUTER_API_KEY=sk-or-...
# - GITHUB_TOKEN=ghp_...
# - TEST_REPO=username/repo
```

### 2. Manuelle Installation

```bash
# Backend + Worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Starten

**Option A: Alles manuell (für Entwicklung)**

```bash
# Terminal 1: Backend
source venv/bin/activate
uvicorn src.kanban.main:app --reload

# Terminal 2: Agent Worker
source venv/bin/activate
python agent_worker.py

# Terminal 3: Frontend
cd frontend
npm start
```

**Option B: Docker Compose (einfacher)**

```bash
docker-compose up --build
```

### 4. Zugriff

- **Kanban Board**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Backend API**: http://localhost:8000

## Verwendung

### Ticket erstellen

1. Öffne http://localhost:3000
2. Klicke "+ Neues Ticket"
3. Fülle Titel, Beschreibung, Kunde, Repository aus
4. Ticket erscheint automatisch in "Backlog"

### Mit KI-Agent kommunizieren

1. Der Agent erkennt neue Tickets automatisch (alle 5 Sekunden)
2. Ticket wird auf "In Progress" gesetzt
3. Der Agent analysiert und kommentiert mit Fragen/Vorschlägen
4. Du antwortest im Ticket-Chat
5. Der Agent setzt die Arbeit fort

### Status-Flow

```
📥 Backlog → 🔨 In Progress → ❓ Rückfrage → 🧪 Testing → ✅ Done
                ↓
         (bei Unklarheit)
```

## Konfiguration

### Agenten-Persönlichkeit (`agents/dev-agent-1/soul.md`)

```markdown
# Seele des Agenten

## Persönlichkeit
- Freundlich, professionell
- Erklärt technische Dinge verständlich

## Kommunikationsstil
- Duzt Kunden
- Verwendet Emojis sparsam
```

### Regeln (`agents/dev-agent-1/rules.md`)

```markdown
# Grundsatzbefehle

## Sicherheit
- Teile NIEMALS Kundendaten mit Dritten
- Keine API-Keys in Code committen
```

## Architektur

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│    Agent    │
│  (React)    │     │  (FastAPI)  │     │   Worker    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                    │                    │
       │                    │                    ▼
       │                    │            ┌─────────────┐
       │                    │            │   Kimi 2.5  │
       │                    │            │  (OpenRouter)│
       │                    │            └─────────────┘
       │                    │
       │                    ▼
       │            ┌─────────────┐
       └───────────▶│  SQLite DB  │
                    └─────────────┘
```

## API Endpunkte

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | /tickets | Alle Tickets |
| POST | /tickets | Ticket erstellen |
| GET | /tickets/{id} | Ticket Details |
| POST | /tickets/{id}/comments | Kommentar hinzufügen |
| GET | /queue/{agent_id} | Agent Queue |

## Fehlersuche

**Agent startet nicht:**
```bash
# Prüfe API Keys
python -c "import os; print('OK' if os.getenv('OPEN_ROUTER_API_KEY') else 'MISSING')"
```

**Frontend kann nicht auf API zugreifen:**
```bash
# Proxy-Einstellung prüfen (package.json)
# Oder REACT_APP_API_URL setzen
```

## Lizenz

MIT
