# Wichtige Links & Ressourcen

## Projekt-Links

### Repository
- **GitHub**: `https://github.com/rinaldisantiago/personal-ki-agents`
- **Lokaler Pfad**: `/home/rin/Work/personal-ki-agents`

### Laufende Services (lokal)
| Service | URL | Beschreibung |
|---------|-----|--------------|
| Kanban Board | http://localhost:3000 | React Frontend |
| API Docs | http://localhost:8000/docs | FastAPI Swagger UI |
| Backend API | http://localhost:8000 | FastAPI Endpunkte |

### Docker Services
```bash
docker-compose up --build
```
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Worker**: background process

## Dokumentation

### Projekt-Pläne (pm/)
| Datei | Beschreibung |
|-------|--------------|
| `pm/Architektur-Projektplan.md` | Gesamtarchitektur & Vision |
| `pm/memory-context-management-plan.md` | Gedächtnis-System Architektur |
| `pm/MVP-Plan-GitHub.md` | GitHub Integration Plan |
| `pm/PM-Tool-Integration-Plan.md` | Kanban/PM Tool Integration |
| `pm/Security-und-MVP-Plan.md` | Security & MVP Anforderungen |
| `pm/Projektplan-KI-Mitarbeiter.md` | Gesamtprojekt Roadmap |
| `pm/03-Bitbucket-Integration.md` | Bitbucket Integration Details |

### README
- `README.md` - Schnellstart & Übersicht

## API Referenzen

### GitHub API
- **Docs**: https://docs.github.com/en/rest
- **Rate Limits**: 5000 requests/hour (authenticated)
- **Token**: `GITHUB_TOKEN` in `.env`

### Bitbucket API
- **Docs**: https://developer.atlassian.com/bitbucket/api/2/reference/
- **Token**: `BITBUCKET_TOKEN` in `.env`

### OpenRouter API
- **Docs**: https://openrouter.ai/docs
- **Model**: `kimi/kimi-k2-5`
- **Key**: `OPEN_ROUTER_API_KEY` in `.env`

### FastAPI (lokal)
- **Docs**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

## Tools & Frameworks

### Python
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **ChromaDB**: https://docs.trychroma.com/
- **Redis Python**: https://redis-py.readthedocs.io/

### React
- **React Docs**: https://react.dev/
- **React Bootstrap**: https://react-bootstrap.github.io/

### DDEV
- **DDEV Docs**: https://ddev.readthedocs.io/
- **Shopware DDEV**: https://ddev.readthedocs.io/en/latest/users/quickstart/#shopware

### Shopware
- **Shopware Docs**: https://developer.shopware.com/docs/
- **Shopware API**: https://shopware.stoplight.io/docs/admin-api

## Development

### Lokale Entwicklung
```bash
# Backend + Worker
source venv/bin/activate
uvicorn src.kanban.main:app --reload  # Terminal 1
python agent_worker.py                 # Terminal 2

# Frontend
cd frontend && npm start               # Terminal 3
```

### Docker
```bash
# Alles auf einmal
docker-compose up --build

# Einzelne Services
docker-compose up backend
docker-compose up frontend
docker-compose up worker
```

### Tests
```bash
# Integration Tests
python test_integration.py

# GitHub Connection Test
python test_github_connection.py

# Unit Tests (Tools)
python -m pytest src/tools/tests/
```

## Environment Variablen

Siehe `.env`:
```bash
OPEN_ROUTER_API_KEY=sk-or-...
GITHUB_TOKEN=ghp_...
KIMI_API_KEY=...
DATABASE_URL=sqlite:///./kanban.db
REDIS_URL=redis://localhost:6379
USE_ENHANCED_AGENT=true
```

## Troubleshooting

### Logs anzeigen
```bash
# Worker Logs
tail -f logs/agent_worker.log

# Docker Logs
docker-compose logs -f worker
```

### Datenbank
```bash
# SQLite direkt
sqlite3 kanban.db

# Redis
redis-cli
> KEYS "*"
```
