# MVP-Plan: KI-Agent mit GitHub-Integration

> **Ziel:** Ein funktionierender Prototyp mit einem Developer-Agenten, GitHub-Integration, einfachem Kanban-Board und Rückfragen-Workflow.
> 
> **Scope:** Lesen + Analysieren + Rückfragen (NO WRITE im MVP)

---

## 1. Test-Projekt Definition

### 1.1 Projekt-Vorschlag: Task Tracker CLI

Ein einfacher **Task Tracker** als CLI-Anwendung in Python:
- Überschaubarer Code (< 500 Zeilen)
- Klare Struktur mit Separation of Concerns
- Einfache Testbarkeit
- Realistische Features für Agent-Übungen

**Warum dieser Projekt-Typ?**
- Jeder versteht das Domain-Problem (Aufgaben verwalten)
- Einfach zu erweitern (API, GUI, Datenbank)
- Gute Basis für Refactoring-Übungen
- Eindeutige Testfälle definierbar

### 1.2 Repository-Struktur

```
task-tracker/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── src/
│   ├── __init__.py
│   ├── cli.py                  # CLI-Interface (argparse)
│   ├── tasks.py                # Task-Logik (Domain)
│   ├── storage.py              # JSON-File Storage
│   └── utils.py                # Hilfsfunktionen
├── tests/
│   ├── __init__.py
│   ├── test_tasks.py           # Unit-Tests für Tasks
│   ├── test_storage.py         # Unit-Tests für Storage
│   └── test_cli.py             # Integration-Tests
├── requirements.txt            # Abhängigkeiten
├── requirements-dev.txt        # Dev-Abhängigkeiten
├── README.md                   # Dokumentation
├── .gitignore
└── pyproject.toml              # Projekt-Konfiguration
```

### 1.3 Beispiel-Code (Starter-Template)

**`src/tasks.py`**
```python
"""Task domain logic."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    description: str = ""
    status: str = "todo"  # todo, in_progress, done
    created_at: str = ""
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class TaskManager:
    def __init__(self, storage):
        self.storage = storage
        self._tasks = []
        self._load()
    
    def _load(self):
        """Load tasks from storage."""
        data = self.storage.load()
        self._tasks = [Task(**item) for item in data]
    
    def _save(self):
        """Save tasks to storage."""
        data = [asdict(task) for task in self._tasks]
        self.storage.save(data)
    
    def create(self, title: str, description: str = "") -> Task:
        """Create a new task."""
        task_id = len(self._tasks) + 1
        task = Task(
            id=task_id,
            title=title,
            description=description
        )
        self._tasks.append(task)
        self._save()
        return task
    
    def list(self, status: Optional[str] = None):
        """List all tasks, optionally filtered by status."""
        if status:
            return [t for t in self._tasks if t.status == status]
        return self._tasks.copy()
    
    def update(self, task_id: int, **kwargs) -> Optional[Task]:
        """Update a task."""
        for task in self._tasks:
            if task.id == task_id:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = datetime.now().isoformat()
                self._save()
                return task
        return None
    
    def delete(self, task_id: int) -> bool:
        """Delete a task."""
        for i, task in enumerate(self._tasks):
            if task.id == task_id:
                self._tasks.pop(i)
                self._save()
                return True
        return False
```

**`src/storage.py`**
```python
"""Storage implementations."""
import json
from pathlib import Path
from typing import List, Dict


class JSONStorage:
    def __init__(self, filepath: str = "tasks.json"):
        self.filepath = Path(filepath)
    
    def load(self) -> List[Dict]:
        """Load data from JSON file."""
        if not self.filepath.exists():
            return []
        with open(self.filepath, 'r') as f:
            return json.load(f)
    
    def save(self, data: List[Dict]):
        """Save data to JSON file."""
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)
```

**`src/cli.py`**
```python
#!/usr/bin/env python3
"""CLI interface for task tracker."""
import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from tasks import TaskManager
from storage import JSONStorage


def main():
    parser = argparse.ArgumentParser(description="Task Tracker CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new task')
    create_parser.add_argument('title', help='Task title')
    create_parser.add_argument('--description', '-d', default='', help='Task description')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List tasks')
    list_parser.add_argument('--status', '-s', choices=['todo', 'in_progress', 'done'], 
                            help='Filter by status')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update a task')
    update_parser.add_argument('id', type=int, help='Task ID')
    update_parser.add_argument('--title', '-t', help='New title')
    update_parser.add_argument('--description', '-d', help='New description')
    update_parser.add_argument('--status', '-s', choices=['todo', 'in_progress', 'done'],
                              help='New status')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a task')
    delete_parser.add_argument('id', type=int, help='Task ID')
    
    args = parser.parse_args()
    
    # Initialize
    storage = JSONStorage()
    manager = TaskManager(storage)
    
    # Execute command
    if args.command == 'create':
        task = manager.create(args.title, args.description)
        print(f"Created task #{task.id}: {task.title}")
    
    elif args.command == 'list':
        tasks = manager.list(args.status)
        if not tasks:
            print("No tasks found.")
        for task in tasks:
            print(f"#{task.id} [{task.status}] {task.title}")
    
    elif args.command == 'update':
        updates = {}
        if args.title:
            updates['title'] = args.title
        if args.description:
            updates['description'] = args.description
        if args.status:
            updates['status'] = args.status
        
        task = manager.update(args.id, **updates)
        if task:
            print(f"Updated task #{task.id}")
        else:
            print(f"Task #{args.id} not found.")
    
    elif args.command == 'delete':
        if manager.delete(args.id):
            print(f"Deleted task #{args.id}")
        else:
            print(f"Task #{args.id} not found.")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
```

**`tests/test_tasks.py`**
```python
"""Tests for tasks module."""
import pytest
from src.tasks import Task, TaskManager


class MockStorage:
    """Mock storage for testing."""
    def __init__(self, data=None):
        self.data = data or []
        self.saved = []
    
    def load(self):
        return self.data
    
    def save(self, data):
        self.saved = data


class TestTask:
    def test_task_creation(self):
        task = Task(id=1, title="Test Task")
        assert task.id == 1
        assert task.title == "Test Task"
        assert task.status == "todo"
        assert task.created_at  # Auto-generated


class TestTaskManager:
    def test_create_task(self):
        storage = MockStorage()
        manager = TaskManager(storage)
        
        task = manager.create("New Task", "Description")
        
        assert task.id == 1
        assert task.title == "New Task"
        assert len(storage.saved) == 1
    
    def test_list_tasks(self):
        storage = MockStorage([
            {'id': 1, 'title': 'Task 1', 'description': '', 'status': 'todo', 'created_at': '2024-01-01'},
            {'id': 2, 'title': 'Task 2', 'description': '', 'status': 'done', 'created_at': '2024-01-02'}
        ])
        manager = TaskManager(storage)
        
        tasks = manager.list()
        assert len(tasks) == 2
        
        done_tasks = manager.list(status='done')
        assert len(done_tasks) == 1
        assert done_tasks[0].title == 'Task 2'
    
    def test_update_task(self):
        storage = MockStorage([
            {'id': 1, 'title': 'Old Title', 'description': '', 'status': 'todo', 'created_at': '2024-01-01'}
        ])
        manager = TaskManager(storage)
        
        task = manager.update(1, title='New Title', status='done')
        
        assert task is not None
        assert task.title == 'New Title'
        assert task.status == 'done'
    
    def test_update_nonexistent_task(self):
        storage = MockStorage()
        manager = TaskManager(storage)
        
        task = manager.update(999, title='New Title')
        
        assert task is None
    
    def test_delete_task(self):
        storage = MockStorage([
            {'id': 1, 'title': 'Task 1', 'description': '', 'status': 'todo', 'created_at': '2024-01-01'}
        ])
        manager = TaskManager(storage)
        
        result = manager.delete(1)
        
        assert result is True
        assert len(storage.saved) == 0
```

**`pyproject.toml`**
```toml
[project]
name = "task-tracker"
version = "0.1.0"
description = "A simple CLI task tracker"
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]

[tool.black]
line-length = 100
target-version = ['py39']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "--cov=src --cov-report=term-missing"
```

### 1.4 Beispiel-Tickets für den Agenten

| ID | Titel | Typ | Beschreibung | Geschätzter Aufwand |
|---|---|---|---|---|
| **TT-1** | Prioritäts-Feld hinzufügen | Feature | Füge ein `priority` Feld zu Tasks hinzu (low/medium/high). Aktualisiere CLI und Tests. | Klein |
| **TT-2** | JSON-Speicher mit Backup | Enhancement | Bevor die JSON-Datei überschrieben wird, erstelle ein Backup (`.bak`). | Klein |
| **TT-3** | Task-Suche implementieren | Feature | Neuer Befehl `search <query>` um Tasks nach Titel zu durchsuchen. | Mittel |
| **TT-4** | CLI-Output formatieren | Enhancement | Bessere Formatierung mit `rich` oder Tabulate für schönere Tabellen. | Klein |
| **TT-5** | Refactor: TaskStatus als Enum | Refactoring | Ersetze String-Status durch ein `TaskStatus` Enum für Typsicherheit. | Mittel |
| **TT-6** | Fehlerbehandlung verbessern | Bugfix | Füge spezifische Exceptions hinzu statt `None` zurückzugeben. | Mittel |
| **TT-7** | Config-File Support | Feature | Lese Konfiguration aus `.tasktrackerrc` (z.B. für Standard-Dateipfad). | Mittel |
| **TT-8** | Unit-Tests erweitern | Testing | Erhöhe Test-Coverage auf >90%, füge Edge-Case-Tests hinzu. | Klein |

---

## 2. MVP Architektur

### 2.1 Vereinfachte High-Level-Architektur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Kanban-Board (Web-UI)                                              │    │
│  │  • Ticket-Übersicht anzeigen                                        │    │
│  │  • Agent-Status anzeigen                                            │    │
│  │  • Rückfragen-Dialog                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ HTTP/WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENTIC WORKFLOW ENGINE                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Developer Agent (Einzelner Agent im MVP)                           │    │
│  │                                                                     │    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │    │
│  │  │ OBSERVE  │───▶│  REASON  │───▶│   PLAN   │───▶│   ACT    │      │    │
│  │  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │    │
│  │       │                                                    │        │    │
│  │       │              ┌─────────────────┐                   │        │    │
│  │       └─────────────▶│   RÜCKFRAGEN    │◀──────────────────┘        │    │
│  │                      │   WORKFLOW      │                            │    │
│  │                      └─────────────────┘                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Memory & Context                                                   │    │
│  │  • Short-term: Session-Cache                                        │    │
│  │  • Long-term: SQLite (Ticket-Status, Rückfragen-Historie)           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ API Calls
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GIT ADAPTER LAYER (GitHub)                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  GitHub Adapter                                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │    │
│  │  │ Repos       │  │ Issues      │  │ Pull Req.   │  │ Contents   │  │    │
│  │  │ • get_repo  │  │ • list      │  │ • list      │  │ • get_file │  │    │
│  │  │ • list      │  │ • get       │  │ • get       │  │ • get_tree │  │    │
│  │  │             │  │ • comments  │  │ • comments  │  │ • readme   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                   │                                         │
│                                   ▼ REST API                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         GITHUB.COM                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Komponenten-Diagramm (C4-Style Component)

```
                    ┌─────────────────────────────────────┐
                    │     Kanban Board (Web UI)           │
                    │  ┌─────────────────────────────┐   │
                    │  │ Ticket List View            │   │
                    │  │ Agent Status Dashboard      │   │
                    │  │ Clarification Dialog        │   │
                    │  └─────────────────────────────┘   │
                    └─────────────┬───────────────────────┘
                                  │
                                  │ HTTP/REST
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Agent Service (Python/FastAPI)                     │
│                                                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │  Ticket Controller  │  │  Agent Controller   │  │  Clarification API  │   │
│  │  ─────────────────  │  │  ─────────────────  │  │  ─────────────────  │   │
│  │  GET /tickets       │  │  POST /agent/start  │  │  POST /clarify      │   │
│  │  GET /tickets/:id   │  │  POST /agent/pause  │  │  GET /pending-q     │   │
│  │  PUT /tickets/:id   │  │  GET /agent/status  │  │                     │   │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘   │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                      ORPA Workflow Engine                                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │  │
│  │  │ Observer    │─▶│ Reasoner    │─▶│ Planner     │─▶│ Actor (NO WRITE)│  │  │
│  │  │ ─────────── │  │ ─────────── │  │ ─────────── │  │ ────────────── │  │  │
│  │  │ Fetch Issue │  │ Analyze     │  │ Create Plan │  │ Analyze Only   │  │  │
│  │  │ Get Code    │  │ Req/Context │  │ Est. Effort │  │ No Code Change │  │  │
│  │  │ Read Files  │  │ Identify    │  │             │  │                │  │  │
│  │  │             │  │ Blockers    │  │             │  │                │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────────┘  │  │
│  │                                                                          │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    LLM Client (OpenRouter)                          │  │  │
│  │  │  • GPT-5 für Reasoning                                            │  │  │
│  │  │  • Claude für Code-Analysis                                       │  │  │
│  │  │  • Kimi 2.5 für schnelle Tasks                                    │  │  │
│  │  └────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │  Ticket Repository  │  │  Memory Store       │  │  Clarification Repo │   │
│  │  ─────────────────  │  │  ─────────────────  │  │  ─────────────────  │   │
│  │  SQLite (Local)     │  │  SQLite / Redis     │  │  SQLite (Local)     │   │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘   │
│                                                                               │
└───────────────────────────────────┬───────────────────────────────────────────┘
                                    │
                                    │ REST API
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Git Adapter Layer                                   │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     GitHub Adapter (MVP)                                 │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │  │
│  │  │ Repository API   │  │ Issues API       │  │ Contents API     │      │  │
│  │  │ ──────────────── │  │ ──────────────── │  │ ──────────────── │      │  │
│  │  │ get_repository() │  │ list_issues()    │  │ get_file()       │      │  │
│  │  │ list_branches()  │  │ get_issue()      │  │ get_directory()  │      │  │
│  │  │                  │  │ list_comments()  │  │ get_readme()     │      │  │
│  │  │                  │  │ create_comment() │  │                  │      │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘      │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     Bitbucket Adapter (Zukunft)                          │  │
│  │  • Interface-identisch mit GitHub Adapter                                │  │
│  │  • Nur API-Endpunkte anders                                              │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Datenfluss: Ticket-Analyse mit Rückfragen

```
┌─────────┐     ┌─────────────┐     ┌───────────────┐     ┌─────────────────┐
│  User   │────▶│ Kanban-Board│────▶│ Agent-Service │────▶│  ORPA Engine    │
│         │     │ (Ticket     │     │ (Orchestrator)│     │                 │
│         │     │  auswählen) │     │               │     │                 │
└─────────┘     └─────────────┘     └───────────────┘     └────────┬────────┘
                                                                   │
                    ┌────────────────────────────────────────────────┐
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ORPA SCHLEIFE                                   │
│                                                                              │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│   │ OBSERVE  │─────▶│  REASON  │─────▶│   PLAN   │─────▶│   ACT    │       │
│   └──────────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘       │
│        │                 │                 │                  │            │
│        │                 │                 │                  │            │
│   • Hole Ticket     • Analysiere      • Schätze Aufwand   • Erstelle      │
│     von GitHub        Anforderungen     • Identifiziere     Analyse-      │
│   • Lese Code       • Identifiziere       Blocker           Bericht        │
│   • Sammle Context    Unklarheiten    • Plane nächste     • POSTe         │
│                                            Schritte         Kommentar      │
│                         │                                                      │
│                         │                                                      │
│                         ▼                                                      │
│                  ┌───────────────┐                                             │
│                  │  Unklar?      │                                             │
│                  │  ───────────  │                                             │
│                  │  JA ────────▶ │ RÜCKFRAGE-Workflow                          │
│                  │               │ • Erstelle Frage                            │
│                  │  NEIN ──────▶ │ • Speichere in DB                           │
│                  │   Weiter...   │ • Zeige im Board                            │
│                  └───────────────┘ • Warte auf Antwort                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Steps (Woche 1-4)

### Woche 1: Setup & GitHub-Integration

#### Tag 1-2: Projekt-Setup

| Task | Beschreibung | Output |
|------|--------------|--------|
| **1.1** | Repository-Struktur erstellen | `kimi-agent/` mit `src/`, `tests/`, `docs/` |
| **1.2** | Python-Projekt initieren | `pyproject.toml`, virtuelle Umgebung |
| **1.3** | Docker-Setup | `Dockerfile`, `docker-compose.yml` für Entwicklung |
| **1.4** | Linting & Formatting | `black`, `flake8`, `mypy` konfiguriert |

#### Tag 3-5: GitHub-Adapter

```python
# src/adapters/github/client.py
"""GitHub API Client with unified interface."""
from typing import List, Dict, Optional
import requests
from dataclasses import dataclass


@dataclass
class GitHubConfig:
    token: str
    base_url: str = "https://api.github.com"
    owner: str = ""
    repo: str = ""


class GitHubClient:
    """GitHub API client implementing the Git Adapter Interface."""
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to GitHub API."""
        url = f"{self.config.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    # Repository Operations
    def get_repository(self, owner: str = None, repo: str = None) -> Dict:
        """Get repository information."""
        owner = owner or self.config.owner
        repo = repo or self.config.repo
        return self._request("GET", f"/repos/{owner}/{repo}")
    
    # Issue Operations
    def list_issues(self, state: str = "open", **filters) -> List[Dict]:
        """List issues in the repository."""
        params = {"state": state, **filters}
        return self._request(
            "GET", 
            f"/repos/{self.config.owner}/{self.config.repo}/issues",
            params=params
        )
    
    def get_issue(self, issue_number: int) -> Dict:
        """Get a specific issue."""
        return self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/issues/{issue_number}"
        )
    
    def list_issue_comments(self, issue_number: int) -> List[Dict]:
        """List comments on an issue."""
        return self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/issues/{issue_number}/comments"
        )
    
    def create_comment(self, issue_number: int, body: str) -> Dict:
        """Create a comment on an issue."""
        return self._request(
            "POST",
            f"/repos/{self.config.owner}/{self.config.repo}/issues/{issue_number}/comments",
            json={"body": body}
        )
    
    # Content Operations (READ-ONLY im MVP)
    def get_file_content(self, path: str, ref: str = "main") -> str:
        """Get content of a file."""
        result = self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/contents/{path}",
            params={"ref": ref}
        )
        import base64
        return base64.b64decode(result["content"]).decode("utf-8")
    
    def get_directory_contents(self, path: str = "", ref: str = "main") -> List[Dict]:
        """List contents of a directory."""
        return self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/contents/{path}",
            params={"ref": ref}
        )
    
    def get_readme(self, ref: str = "main") -> str:
        """Get README content."""
        return self.get_file_content("README.md", ref)
    
    def get_repo_tree(self, ref: str = "main", recursive: bool = True) -> List[Dict]:
        """Get repository file tree."""
        result = self._request(
            "GET",
            f"/repos/{self.config.owner}/{self.config.repo}/git/trees/{ref}",
            params={"recursive": "1" if recursive else "0"}
        )
        return result.get("tree", [])
```

| Task | Beschreibung | Output |
|------|--------------|--------|
| **1.5** | GitHub-Client implementieren | `GitHubClient` Klasse mit allen READ-Operationen |
| **1.6** | Adapter-Interface definieren | `BaseGitAdapter` abstrakte Klasse |
| **1.7** | Unit-Tests für Adapter | pytest-Tests mit Mock-Responses |

#### Tag 6-7: Einfaches Kanban-Board (Grundgerüst)

```python
# src/board/simple_board.py
"""Simple Kanban board using SQLite backend."""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
import sqlite3
import json


@dataclass
class Ticket:
    id: str
    title: str
    description: str
    status: str  # backlog, todo, in_progress, review, done
    source: str  # github, bitbucket, manual
    external_id: str  # issue number
    external_url: str
    agent_status: str = "idle"  # idle, analyzing, waiting_for_clarification
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class SimpleKanbanBoard:
    """SQLite-based Kanban board for MVP."""
    
    def __init__(self, db_path: str = "kanban.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'backlog',
                    source TEXT,
                    external_id TEXT,
                    external_url TEXT,
                    agent_status TEXT DEFAULT 'idle',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clarifications (
                    id TEXT PRIMARY KEY,
                    ticket_id TEXT,
                    question TEXT,
                    answer TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    answered_at TEXT,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
                )
            """)
    
    def create_ticket(self, ticket: Ticket) -> Ticket:
        """Create a new ticket."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tickets 
                (id, title, description, status, source, external_id, external_url, 
                 agent_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket.id, ticket.title, ticket.description, ticket.status,
                ticket.source, ticket.external_id, ticket.external_url,
                ticket.agent_status, ticket.created_at, ticket.updated_at
            ))
        return ticket
    
    def get_ticket(self, ticket_id: str) -> Optional[Ticket]:
        """Get a ticket by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            )
            row = cursor.fetchone()
            if row:
                return Ticket(*row)
        return None
    
    def list_tickets(self, status: Optional[str] = None) -> List[Ticket]:
        """List tickets, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            if status:
                cursor = conn.execute(
                    "SELECT * FROM tickets WHERE status = ? ORDER BY created_at",
                    (status,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM tickets ORDER BY created_at"
                )
            return [Ticket(*row) for row in cursor.fetchall()]
    
    def update_ticket_status(self, ticket_id: str, status: str):
        """Update ticket status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), ticket_id)
            )
    
    def update_agent_status(self, ticket_id: str, agent_status: str):
        """Update agent working status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE tickets SET agent_status = ?, updated_at = ? WHERE id = ?",
                (agent_status, datetime.now().isoformat(), ticket_id)
            )
    
    def sync_from_github(self, github_client) -> List[Ticket]:
        """Sync issues from GitHub to local board."""
        issues = github_client.list_issues(state="open")
        tickets = []
        for issue in issues:
            # Skip pull requests (they appear as issues)
            if "pull_request" in issue:
                continue
            
            ticket_id = f"GH-{issue['number']}"
            ticket = Ticket(
                id=ticket_id,
                title=issue["title"],
                description=issue["body"] or "",
                status="backlog",
                source="github",
                external_id=str(issue["number"]),
                external_url=issue["html_url"]
            )
            
            # Insert or update
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tickets 
                    (id, title, description, status, source, external_id, external_url,
                     agent_status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 
                            COALESCE((SELECT agent_status FROM tickets WHERE id = ?), 'idle'),
                            COALESCE((SELECT created_at FROM tickets WHERE id = ?), ?),
                            ?)
                """, (ticket.id, ticket.title, ticket.description, ticket.status,
                      ticket.source, ticket.external_id, ticket.external_url,
                      ticket.id, ticket.id, ticket.created_at, ticket.updated_at))
            
            tickets.append(ticket)
        return tickets
```

| Task | Beschreibung | Output |
|------|--------------|--------|
| **1.8** | SQLite-basiertes Board | `SimpleKanbanBoard` mit Tickets & Status |
| **1.9** | GitHub-Sync | `sync_from_github()` Methode |
| **1.10** | CLI für Board | `kimi board sync`, `kimi board list` |

**Woche 1 Deliverable:**
- [x] GitHub-Client kann Issues lesen
- [x] Lokales Kanban-Board mit SQLite
- [x] Sync zwischen GitHub und lokalem Board

---

### Woche 2: Agent-Grundgerüst + ORPA

#### Tag 8-10: LLM-Integration (OpenRouter)

```python
# src/llm/openrouter_client.py
"""OpenRouter client with model switching."""
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import requests
import json


@dataclass
class LLMMessage:
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict
    cost_usd: float


class OpenRouterClient:
    """OpenRouter API client with cost-effective model switching."""
    
    MODELS = {
        "gpt-5": "openai/gpt-5",
        "claude-sonnet": "anthropic/claude-3.5-sonnet",
        "claude-opus": "anthropic/claude-3-opus",
        "kimi-25": "moonshot/kimi-2.5",
        "gemini-pro": "google/gemini-2.0-pro-exp-02-05",
    }
    
    # Approximate costs per 1M tokens (input/output)
    COSTS = {
        "openai/gpt-5": (5.0, 15.0),
        "anthropic/claude-3.5-sonnet": (3.0, 15.0),
        "anthropic/claude-3-opus": (15.0, 75.0),
        "moonshot/kimi-2.5": (0.5, 2.0),
        "google/gemini-2.0-pro-exp-02-05": (0.0, 0.0),  # Free tier
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kimi-agent.local",
            "X-Title": "Kimi Agent MVP"
        })
    
    def chat_completion(
        self,
        messages: List[LLMMessage],
        model: str = "moonshot/kimi-2.5",
        temperature: float = 0.7,
        max_tokens: int = 4000,
        tools: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """Send chat completion request."""
        
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        response = self.session.post(
            f"{self.base_url}/chat/completions",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        # Calculate cost
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data["model"],
            usage=usage,
            cost_usd=cost
        )
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate approximate cost in USD."""
        input_cost, output_cost = self.COSTS.get(model, (0, 0))
        return (input_tokens / 1_000_000 * input_cost + 
                output_tokens / 1_000_000 * output_cost)
    
    def quick_completion(self, prompt: str, model: str = "moonshot/kimi-2.5") -> str:
        """Quick single-turn completion."""
        messages = [LLMMessage(role="user", content=prompt)]
        response = self.chat_completion(messages, model=model)
        return response.content
```

| Task | Beschreibung | Output |
|------|--------------|--------|
| **2.1** | OpenRouter-Client | `OpenRouterClient` mit Modell-Switching |
| **2.2** | Kosten-Tracking | Pro-Request-Kostenberechnung |
| **2.3** | Model-Router | Simple Routing-Logik (Standard → Premium bei Bedarf) |

#### Tag 11-14: ORPA Engine Implementierung

```python
# src/agent/orpa_engine.py
"""ORPA (Observe-Reason-Plan-Act) workflow engine."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
import json
from datetime import datetime


class ORPAState(Enum):
    IDLE = "idle"
    OBSERVING = "observing"
    REASONING = "reasoning"
    PLANNING = "planning"
    ACTING = "acting"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Observation:
    """Data collected during observation phase."""
    ticket_data: Dict
    code_files: List[Dict] = field(default_factory=list)
    readme_content: str = ""
    existing_comments: List[Dict] = field(default_factory=list)
    repository_structure: List[Dict] = field(default_factory=list)
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class Reasoning:
    """Analysis and insights from reasoning phase."""
    ticket_summary: str = ""
    complexity_assessment: str = ""
    identified_blockers: List[str] = field(default_factory=list)
    required_files: List[str] = field(default_factory=list)
    unclear_aspects: List[str] = field(default_factory=list)
    estimated_effort: str = ""
    confidence_score: float = 0.0  # 0.0 - 1.0
    needs_clarification: bool = False
    reasoning_log: str = ""


@dataclass
class Plan:
    """Execution plan."""
    steps: List[Dict] = field(default_factory=list)
    estimated_duration: str = ""
    dependencies: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class Action:
    """Executed actions."""
    type: str  # "analysis", "comment", "clarification_request"
    description: str
    output: str
    status: str = "pending"  # pending, completed, failed
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ORPAContext:
    """Full context of an ORPA cycle."""
    ticket_id: str
    state: ORPAState = ORPAState.IDLE
    observation: Optional[Observation] = None
    reasoning: Optional[Reasoning] = None
    plan: Optional[Plan] = None
    actions: List[Action] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    
    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()


class ORPAEngine:
    """ORPA workflow engine for agent execution."""
    
    SYSTEM_PROMPT_OBSERVE = """You are analyzing a software development ticket. 
Your task is to observe and collect all relevant information.

Analyze the ticket and repository to understand:
1. What is being requested?
2. What files are likely involved?
3. What is the current state of the codebase?

Be thorough but concise in your observations."""

    SYSTEM_PROMPT_REASON = """You are analyzing a software development ticket based on observations.

Your reasoning should include:
1. Summary of the requirement
2. Complexity assessment (Low/Medium/High)
3. Any blockers or unclear requirements
4. Files that need to be examined or modified
5. Confidence level (0.0-1.0)
6. Whether clarification is needed before proceeding

If something is unclear, explicitly state what questions need to be answered."""

    SYSTEM_PROMPT_PLAN = """You are planning the implementation of a software development ticket.

Create a step-by-step plan that includes:
1. Analysis steps (code review, understanding existing patterns)
2. Implementation steps (if no clarification needed)
3. Testing approach
4. Estimated effort
5. Potential risks

Format as a structured plan with clear steps."""

    def __init__(self, llm_client, git_client):
        self.llm = llm_client
        self.git = git_client
        self.contexts: Dict[str, ORPAContext] = {}
    
    def start_cycle(self, ticket_id: str, ticket_data: Dict) -> ORPAContext:
        """Start a new ORPA cycle."""
        context = ORPAContext(ticket_id=ticket_id)
        self.contexts[ticket_id] = context
        return context
    
    def observe(self, context: ORPAContext) -> Observation:
        """Observe phase: collect all relevant data."""
        context.state = ORPAState.OBSERVING
        
        # Get ticket data
        issue_number = int(context.ticket_id.split("-")[1])
        ticket_data = self.git.get_issue(issue_number)
        
        # Get repository structure
        repo_tree = self.git.get_repo_tree()
        
        # Get README
        try:
            readme = self.git.get_readme()
        except:
            readme = "No README found"
        
        # Get relevant code files (heuristic: look at file extensions)
        code_files = []
        for item in repo_tree:
            if item.get("type") == "blob":
                path = item.get("path", "")
                # Prioritize Python files for this project
                if path.endswith(".py") and "/test" not in path:
                    try:
                        content = self.git.get_file_content(path)
                        code_files.append({
                            "path": path,
                            "content": content[:5000]  # Limit size
                        })
                    except:
                        pass
        
        # Get existing comments
        comments = self.git.list_issue_comments(issue_number)
        
        observation = Observation(
            ticket_data=ticket_data,
            code_files=code_files[:10],  # Limit to first 10 relevant files
            readme_content=readme[:5000],
            existing_comments=comments,
            repository_structure=repo_tree[:100]  # Limit
        )
        
        context.observation = observation
        return observation
    
    def reason(self, context: ORPAContext) -> Reasoning:
        """Reason phase: analyze and identify blockers."""
        context.state = ORPAState.REASONING
        
        obs = context.observation
        
        # Build prompt
        prompt = f"""Ticket: {obs.ticket_data.get('title', 'Unknown')}
Description: {obs.ticket_data.get('body', 'No description')}

Repository Structure:
"""
        for item in obs.repository_structure[:20]:
            prompt += f"- {item.get('path', 'unknown')}\n"
        
        prompt += f"\nREADME:\n{obs.readme_content[:2000]}\n"
        
        prompt += "\nKey Code Files:\n"
        for f in obs.code_files[:5]:
            prompt += f"\n--- {f['path']} ---\n{f['content'][:1000]}\n"
        
        # Get LLM reasoning
        from src.llm.openrouter_client import LLMMessage
        messages = [
            LLMMessage(role="system", content=self.SYSTEM_PROMPT_REASON),
            LLMMessage(role="user", content=prompt)
        ]
        
        response = self.llm.chat_completion(
            messages=messages,
            model="moonshot/kimi-2.5",
            temperature=0.3
        )
        
        # Parse reasoning (simplified - in production use structured output)
        reasoning_text = response.content
        
        # Extract key points (simplified parsing)
        reasoning = Reasoning(
            ticket_summary=obs.ticket_data.get('title', ''),
            reasoning_log=reasoning_text,
            confidence_score=0.7  # Default, would be parsed from LLM
        )
        
        # Check if clarification is needed
        clarification_keywords = [
            "unclear", "ambiguous", "need clarification", 
            "questions", "not specified", "missing information"
        ]
        reasoning.needs_clarification = any(
            kw in reasoning_text.lower() for kw in clarification_keywords
        )
        
        if reasoning.needs_clarification:
            # Extract questions (simplified)
            lines = reasoning_text.split('\n')
            reasoning.unclear_aspects = [
                line.strip('- ').strip() 
                for line in lines 
                if '?' in line or any(kw in line.lower() for kw in clarification_keywords)
            ][:5]  # Limit to 5 questions
        
        context.reasoning = reasoning
        return reasoning
    
    def plan(self, context: ORPAContext) -> Plan:
        """Plan phase: create execution plan."""
        context.state = ORPAState.PLANNING
        
        if context.reasoning.needs_clarification:
            # Planning is limited without clarification
            plan = Plan(
                steps=[
                    {"order": 1, "action": "Wait for clarification", "status": "blocked"},
                    {"order": 2, "action": "Re-analyze after clarification", "status": "pending"}
                ],
                estimated_duration="Unknown - awaiting clarification"
            )
        else:
            # Create full plan
            # (In production, would get this from LLM)
            plan = Plan(
                steps=[
                    {"order": 1, "action": "Analyze existing code patterns", "status": "ready"},
                    {"order": 2, "action": "Design implementation approach", "status": "pending"},
                    {"order": 3, "action": "Implement changes", "status": "pending"},
                    {"order": 4, "action": "Add/update tests", "status": "pending"},
                    {"order": 5, "action": "Verify implementation", "status": "pending"}
                ],
                estimated_duration="2-4 hours"
            )
        
        context.plan = plan
        return plan
    
    def act(self, context: ORPAContext) -> List[Action]:
        """Act phase: execute actions (read-only in MVP)."""
        context.state = ORPAState.ACTING
        
        actions = []
        
        # MVP: Only create analysis comment, no code changes
        analysis = f"""## 🤖 Agent Analysis

### Ticket Summary
{context.reasoning.ticket_summary}

### Complexity Assessment
{context.reasoning.complexity_assessment or 'Medium - requires understanding of existing code structure'}

### Files Involved
"""
        for f in context.observation.code_files[:5]:
            analysis += f"- `{f['path']}`\n"
        
        if context.reasoning.needs_clarification:
            analysis += "\n### ⚠️ Clarification Needed\n\n"
            for q in context.reasoning.unclear_aspects:
                analysis += f"- {q}\n"
            analysis += "\n**Please respond to continue.**"
        else:
            analysis += f"\n### Suggested Approach\n{context.plan.steps}\n"
        
        # Post comment to GitHub
        issue_number = int(context.ticket_id.split("-")[1])
        try:
            self.git.create_comment(issue_number, analysis)
            action = Action(
                type="comment",
                description="Posted analysis comment",
                output=analysis,
                status="completed"
            )
        except Exception as e:
            action = Action(
                type="comment",
                description="Failed to post analysis comment",
                output=str(e),
                status="failed"
            )
        
        actions.append(action)
        context.actions = actions
        
        # Update state
        if context.reasoning.needs_clarification:
            context.state = ORPAState.WAITING_FOR_CLARIFICATION
        else:
            context.state = ORPAState.COMPLETED
        
        context.completed_at = datetime.now().isoformat()
        return actions
    
    def run_full_cycle(self, ticket_id: str, ticket_data: Dict) -> ORPAContext:
        """Run complete ORPA cycle."""
        context = self.start_cycle(ticket_id, ticket_data)
        
        self.observe(context)
        self.reason(context)
        self.plan(context)
        self.act(context)
        
        return context
```

| Task | Beschreibung | Output |
|------|--------------|--------|
| **2.4** | ORPA-States definieren | Enum mit allen Zuständen |
| **2.5** | Observer implementieren | Sammelt Ticket + Code + Struktur |
| **2.6** | Reasoner implementieren | Analysiert + identifiziert Blocker |
| **2.7** | Planner implementieren | Erstellt Arbeitsschritte |
| **2.8** | Actor implementieren (NO WRITE) | Postet nur Kommentare |
| **2.9** | Integrationstests | End-to-End ORPA Test |

**Woche 2 Deliverable:**
- [x] Agent kann ORPA-Schleife durchlaufen
- [x] LLM-Integration mit OpenRouter
- [x] Analyse-Kommentare werden auf GitHub gepostet

---

### Woche 3: Rückfragen-Workflow

#### Tag 15-17: Clarification System

```python
# src/agent/clarification.py
"""Clarification request and response system."""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import sqlite3


@dataclass
class ClarificationRequest:
    """A request for clarification from the agent."""
    id: str
    ticket_id: str
    question: str
    context: str  # Why is this question being asked?
    priority: str  # low, medium, high, blocker
    status: str  # pending, answered, dismissed
    created_at: str = ""
    answered_at: Optional[str] = None
    answer: Optional[str] = None
    answered_by: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class ClarificationStore:
    """SQLite-based store for clarification requests."""
    
    def __init__(self, db_path: str = "clarifications.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clarification_requests (
                    id TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    context TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    answered_at TEXT,
                    answer TEXT,
                    answered_by TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ticket ON clarification_requests(ticket_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON clarification_requests(status)
            """)
    
    def create(self, request: ClarificationRequest) -> ClarificationRequest:
        """Create a new clarification request."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO clarification_requests 
                (id, ticket_id, question, context, priority, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (request.id, request.ticket_id, request.question, 
                  request.context, request.priority, request.status, request.created_at))
        return request
    
    def get(self, request_id: str) -> Optional[ClarificationRequest]:
        """Get a clarification request by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM clarification_requests WHERE id = ?",
                (request_id,)
            )
            row = cursor.fetchone()
            if row:
                return ClarificationRequest(*row)
        return None
    
    def list_by_ticket(self, ticket_id: str, status: Optional[str] = None) -> List[ClarificationRequest]:
        """List clarification requests for a ticket."""
        with sqlite3.connect(self.db_path) as conn:
            if status:
                cursor = conn.execute(
                    """SELECT * FROM clarification_requests 
                       WHERE ticket_id = ? AND status = ?
                       ORDER BY created_at""",
                    (ticket_id, status)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM clarification_requests WHERE ticket_id = ? ORDER BY created_at",
                    (ticket_id,)
                )
            return [ClarificationRequest(*row) for row in cursor.fetchall()]
    
    def answer(self, request_id: str, answer: str, answered_by: str = "user"):
        """Answer a clarification request."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE clarification_requests 
                SET answer = ?, answered_by = ?, status = 'answered', 
                    answered_at = ?
                WHERE id = ?
            """, (answer, answered_by, datetime.now().isoformat(), request_id))
    
    def has_pending(self, ticket_id: str) -> bool:
        """Check if ticket has pending clarification requests."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT COUNT(*) FROM clarification_requests 
                   WHERE ticket_id = ? AND status = 'pending'""",
                (ticket_id,)
            )
            return cursor.fetchone()[0] > 0


class ClarificationWorkflow:
    """Workflow for handling clarifications."""
    
    def __init__(self, store: ClarificationStore, git_client, board):
        self.store = store
        self.git = git_client
        self.board = board
    
    def create_from_analysis(
        self, 
        ticket_id: str, 
        questions: List[str],
        context: str
    ) -> List[ClarificationRequest]:
        """Create clarification requests from agent analysis."""
        import uuid
        
        requests = []
        for i, question in enumerate(questions):
            req = ClarificationRequest(
                id=f"{ticket_id}-Q{i+1}-{uuid.uuid4().hex[:8]}",
                ticket_id=ticket_id,
                question=question,
                context=context,
                priority="blocker" if i == 0 else "high",
                status="pending"
            )
            self.store.create(req)
            requests.append(req)
        
        # Update board status
        self.board.update_agent_status(ticket_id, "waiting_for_clarification")
        
        return requests
    
    def process_answer(self, request_id: str, answer: str, user: str = "user"):
        """Process a user's answer to a clarification request."""
        # Save answer
        self.store.answer(request_id, answer, user)
        
        # Get the request to find ticket
        req = self.store.get(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")
        
        # Check if all clarifications for this ticket are answered
        pending = self.store.list_by_ticket(req.ticket_id, status="pending")
        if not pending:
            # All answered - update board
            self.board.update_agent_status(req.ticket_id, "clarified")
    
    def get_clarification_summary(self, ticket_id: str) -> Dict:
        """Get summary of clarifications for a ticket."""
        all_reqs = self.store.list_by_ticket(ticket_id)
        pending = [r for r in all_reqs if r.status == "pending"]
        answered = [r for r in all_reqs if r.status == "answered"]
        
        return {
            "total": len(all_reqs),
            "pending": len(pending),
            "answered": len(answered),
            "is_complete": len(pending) == 0 and len(answered) > 0,
            "pending_questions": [{"id": r.id, "question": r.question} for r in pending],
            "answers": [{"question": r.question, "answer": r.answer} for r in answered]
        }
    
    def resume_after_clarification(self, ticket_id: str, orpa_engine):
        """Resume ORPA cycle after clarifications are answered."""
        # Get all answers
        summary = self.get_clarification_summary(ticket_id)
        
        if not summary["is_complete"]:
            raise ValueError("Not all clarifications are answered yet")
        
        # Build context with answers
        clarification_context = "\n\n### Clarifications Received:\n\n"
        for item in summary["answers"]:
            clarification_context += f"**Q:** {item['question']}\n"
            clarification_context += f"**A:** {item['answer']}\n\n"
        
        # Restart ORPA with additional context
        ticket_data = {"id": ticket_id, "clarifications": summary}
        context = orpa_engine.start_cycle(ticket_id, ticket_data)
        
        # Mark as ready for next phase
        context.state = ORPAState.REASONING
        
        return context
```

| Task | Beschreibung | Output |
|------|--------------|--------|
| **3.1** | Clarification Model | `ClarificationRequest` Dataclass |
| **3.2** | Clarification Store | SQLite-basierte Speicherung |
| **3.3** | Create-from-Analysis | Automatisches Erstellen von Fragen |
| **3.4** | Answer-Workflow | Verarbeitung von Antworten |

#### Tag 18-19: Web-UI für Rückfragen

```html
<!-- Simple HTML UI for Clarifications -->
<!-- templates/clarifications.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Kimi Agent - Clarifications</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .ticket { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
        .ticket-header { display: flex; justify-content: space-between; align-items: center; }
        .status { padding: 4px 12px; border-radius: 12px; font-size: 12px; }
        .status-waiting { background: #fff3cd; color: #856404; }
        .status-clarified { background: #d4edda; color: #155724; }
        .question { background: #f8f9fa; padding: 12px; border-radius: 4px; margin: 8px 0; }
        .answer-form { margin-top: 8px; }
        .answer-form textarea { width: 100%; padding: 8px; }
        .answer-form button { margin-top: 8px; padding: 8px 16px; }
    </style>
</head>
<body>
    <h1>🤖 Kimi Agent - Pending Clarifications</h1>
    
    <div id="tickets">
        {% for ticket in tickets %}
        <div class="ticket">
            <div class="ticket-header">
                <h3>{{ ticket.id }}: {{ ticket.title }}</h3>
                <span class="status status-{{ ticket.agent_status }}">{{ ticket.agent_status }}</span>
            </div>
            <p>{{ ticket.description[:200] }}...</p>
            <a href="{{ ticket.external_url }}" target="_blank">View on GitHub →</a>
            
            <h4>Clarification Requests:</h4>
            {% for req in ticket.clarifications %}
            <div class="question">
                <p><strong>Q:</strong> {{ req.question }}</p>
                <p><small>{{ req.context }}</small></p>
                
                {% if req.status == 'pending' %}
                <form class="answer-form" onsubmit="submitAnswer(event, '{{ req.id }}')">
                    <textarea name="answer" rows="3" placeholder="Your answer..." required></textarea>
                    <button type="submit">Submit Answer</button>
                </form>
                {% else %}
                <p><strong>A:</strong> {{ req.answer }}</p>
                <small>Answered by {{ req.answered_by }} at {{ req.answered_at }}</small>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}
    </div>

    <script>
        async function submitAnswer(event, requestId) {
            event.preventDefault();
            const form = event.target;
            const answer = form.answer.value;
            
            const response = await fetch(`/api/clarifications/${requestId}/answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer })
            });
            
            if (response.ok) {
                location.reload();
            } else {
                alert('Failed to submit answer');
            }
        }
    </script>
</body>
</html>
```

| Task | Beschreibung | Output |
|------|--------------|--------|
| **3.5** | Web-UI Grundgerüst | Flask/FastAPI Server |
| **3.6** | Clarification-View | HTML-Seite mit offenen Fragen |
| **3.7** | Answer-API | POST-Endpoint für Antworten |

#### Tag 20-21: Integration & Testing

| Task | Beschreibung | Output |
|------|--------------|--------|
| **3.8** | ORPA + Clarification Integration | Nahtloser Workflow |
| **3.9** | Notification-System | (Optional) Email/Slack bei neuen Fragen |
| **3.10** | End-to-End Test | Kompletter Durchlauf mit Rückfragen |

**Woche 3 Deliverable:**
- [x] Agent kann Rückfragen stellen
- [x] Web-UI zeigt offene Fragen
- [x] Antworten werden verarbeitet
- [x] Workflow pausiert/resumed korrekt

---

### Woche 4: Integration & Testing

#### Tag 22-24: API & Integration

```python
# src/api/main.py
"""FastAPI application for Kimi Agent MVP."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

from src.adapters.github.client import GitHubClient, GitHubConfig
from src.board.simple_board import SimpleKanbanBoard
from src.agent.orpa_engine import ORPAEngine
from src.agent.clarification import ClarificationStore, ClarificationWorkflow
from src.llm.openrouter_client import OpenRouterClient

app = FastAPI(title="Kimi Agent MVP", version="0.1.0")

# Dependency injection - in production use proper DI
_config = {
    "github_token": "",
    "github_owner": "",
    "github_repo": "",
    "openrouter_key": ""
}

def get_github_client():
    config = GitHubConfig(
        token=_config["github_token"],
        owner=_config["github_owner"],
        repo=_config["github_repo"]
    )
    return GitHubClient(config)

def get_llm_client():
    return OpenRouterClient(_config["openrouter_key"])

def get_board():
    return SimpleKanbanBoard()

def get_clarification_store():
    return ClarificationStore()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Models
class StartAnalysisRequest(BaseModel):
    ticket_id: str

class AnswerClarificationRequest(BaseModel):
    answer: str

class TicketResponse(BaseModel):
    id: str
    title: str
    status: str
    agent_status: str
    external_url: str

class ClarificationResponse(BaseModel):
    id: str
    question: str
    status: str
    answer: Optional[str]

# Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main dashboard."""
    with open("static/index.html") as f:
        return f.read()

@app.get("/api/tickets", response_model=List[TicketResponse])
async def list_tickets(status: Optional[str] = None):
    """List all tickets."""
    board = get_board()
    tickets = board.list_tickets(status)
    return [
        TicketResponse(
            id=t.id,
            title=t.title,
            status=t.status,
            agent_status=t.agent_status,
            external_url=t.external_url
        )
        for t in tickets
    ]

@app.post("/api/tickets/{ticket_id}/analyze")
async def analyze_ticket(ticket_id: str, background_tasks: BackgroundTasks):
    """Start analysis of a ticket."""
    github = get_github_client()
    llm = get_llm_client()
    board = get_board()
    
    engine = ORPAEngine(llm, github)
    
    # Get ticket data
    issue_number = int(ticket_id.split("-")[1])
    ticket_data = github.get_issue(issue_number)
    
    # Update status
    board.update_agent_status(ticket_id, "analyzing")
    
    # Run in background
    def run_analysis():
        try:
            context = engine.run_full_cycle(ticket_id, ticket_data)
            # Status updated by engine
        except Exception as e:
            board.update_agent_status(ticket_id, f"error: {str(e)}")
    
    background_tasks.add_task(run_analysis)
    
    return {"status": "started", "ticket_id": ticket_id}

@app.get("/api/tickets/{ticket_id}/clarifications")
async def get_clarifications(ticket_id: str):
    """Get clarifications for a ticket."""
    store = get_clarification_store()
    reqs = store.list_by_ticket(ticket_id)
    return [
        ClarificationResponse(
            id=r.id,
            question=r.question,
            status=r.status,
            answer=r.answer
        )
        for r in reqs
    ]

@app.post("/api/clarifications/{request_id}/answer")
async def answer_clarification(request_id: str, req: AnswerClarificationRequest):
    """Answer a clarification request."""
    store = get_clarification_store()
    board = get_board()
    
    workflow = ClarificationWorkflow(store, None, board)
    
    try:
        workflow.process_answer(request_id, req.answer)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sync")
async def sync_with_github():
    """Sync tickets from GitHub."""
    github = get_github_client()
    board = get_board()
    
    tickets = board.sync_from_github(github)
    return {"synced": len(tickets), "tickets": [t.id for t in tickets]}

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}
```

| Task | Beschreibung | Output |
|------|--------------|--------|
| **4.1** | FastAPI Server | REST-API für alle Operationen |
| **4.2** | Background Tasks | Async Ticket-Analyse |
| **4.3** | Config Management | `.env` oder Config-File |

#### Tag 25-26: Docker & Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY static/ ./static/
COPY pyproject.toml .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  kimi-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_OWNER=${GITHUB_OWNER}
      - GITHUB_REPO=${GITHUB_REPO}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

| Task | Beschreibung | Output |
|------|--------------|--------|
| **4.4** | Dockerfile | Container-Build |
| **4.5** | docker-compose.yml | Lokale Entwicklung |
| **4.6** | Deployment-Doku | Setup-Anleitung |

#### Tag 27-28: Testing & Dokumentation

| Task | Beschreibung | Output |
|------|--------------|--------|
| **4.7** | Unit-Tests | >80% Coverage |
| **4.8** | Integration-Tests | API + GitHub Mock |
| **4.9** | E2E-Tests | Playwright für UI |
| **4.10** | README.md | Setup & Usage |
| **4.11** | Architektur-Doku | Diagramme & Entscheidungen |

**Woche 4 Deliverable:**
- [x] API läuft stabil
- [x] Docker-Deployment funktioniert
- [x] Tests passieren
- [x] Dokumentation komplett

---

## 4. Was der Nutzer braucht

### 4.1 GitHub Account

- Standard GitHub Account (kostenlos)
- Für private Repositories: GitHub Pro oder Organisation

### 4.2 Personal Access Token (PAT)

**Schritte:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)"
3. Scopes auswählen:
   - ✅ `repo` - Full control of private repositories
   - ✅ `read:org` - Read org and team membership (falls org repos)
4. Token kopieren und sicher speichern

**Token-Beispiel:**
```bash
# .env Datei erstellen
cat > .env << 'EOF'
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_OWNER=dein-username
GITHUB_REPO=task-tracker
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx
EOF
```

### 4.3 Test-Repository Setup

**Option A: Eigenes Repository erstellen**
```bash
# 1. Repository auf GitHub erstellen (leer)
# 2. Lokal clonen
git clone https://github.com/DEIN-USERNAME/task-tracker.git
cd task-tracker

# 3. Starter-Code kopieren (aus diesem Plan)
# 4. Commit & Push
git add .
git commit -m "Initial commit"
git push origin main
```

**Option B: Template verwenden**
```bash
# Nutze GitHub Template (falls verfügbar)
# oder forke ein Beispiel-Repo
```

### 4.4 OpenRouter Account

1. [openrouter.ai](https://openrouter.ai) besuchen
2. Account erstellen
3. API Key generieren
4. Credits aufladen (für MVP: $5-10 ausreichend)

### 4.5 Checkliste: Nutzer-Setup

- [ ] GitHub Account vorhanden
- [ ] Personal Access Token erstellt (`repo` scope)
- [ ] Test-Repository erstellt und gepusht
- [ ] Beispiel-Tickets in GitHub erstellt
- [ ] OpenRouter Account mit API Key
- [ ] `.env` Datei mit allen Credentials
- [ ] Docker Desktop installiert (optional)

---

## 5. Migration zu Bitbucket später

### 5.1 Git Adapter Interface

Das Git-Adapter-Pattern ermöglicht einfachen Provider-Wechsel:

```python
# src/adapters/base.py
from abc import ABC, abstractmethod
from typing import List, Dict


class BaseGitAdapter(ABC):
    """Abstract base class for Git providers."""
    
    @abstractmethod
    def get_repository(self, owner: str, repo: str) -> Dict:
        """Get repository information."""
        pass
    
    @abstractmethod
    def list_issues(self, state: str = "open", **filters) -> List[Dict]:
        """List issues/tickets."""
        pass
    
    @abstractmethod
    def get_issue(self, issue_number: int) -> Dict:
        """Get a specific issue."""
        pass
    
    @abstractmethod
    def list_issue_comments(self, issue_number: int) -> List[Dict]:
        """List comments on an issue."""
        pass
    
    @abstractmethod
    def create_comment(self, issue_number: int, body: str) -> Dict:
        """Create a comment on an issue."""
        pass
    
    @abstractmethod
    def get_file_content(self, path: str, ref: str = "main") -> str:
        """Get content of a file."""
        pass
    
    @abstractmethod
    def get_directory_contents(self, path: str = "", ref: str = "main") -> List[Dict]:
        """List contents of a directory."""
        pass
    
    @abstractmethod
    def get_repo_tree(self, ref: str = "main", recursive: bool = True) -> List[Dict]:
        """Get repository file tree."""
        pass
```

### 5.2 Unterschiede: GitHub vs Bitbucket

| Aspekt | GitHub | Bitbucket |
|--------|--------|-----------|
| **API Base URL** | `api.github.com` | `api.bitbucket.org/2.0` |
| **Authentication** | `Authorization: token XXX` | `Authorization: Bearer XXX` |
| **Issue Endpoint** | `/repos/{owner}/{repo}/issues` | `/repositories/{workspace}/{repo}/issues` |
| **Response Format** | Direct JSON | Wrapped in `values` array |
| **Pagination** | `page` & `per_page` | `page` & `pagelen` |
| **Comments** | Issue comments | Separate Comments API |
| **Webhooks** | Repository level | Repository level (similar) |

### 5.3 Bitbucket Adapter (Zukünftig)

```python
# src/adapters/bitbucket/client.py
"""Bitbucket API Client implementing BaseGitAdapter."""
from typing import List, Dict
import requests
from dataclasses import dataclass

from src.adapters.base import BaseGitAdapter


@dataclass
class BitbucketConfig:
    token: str
    workspace: str
    repo_slug: str
    base_url: str = "https://api.bitbucket.org/2.0"


class BitbucketAdapter(BaseGitAdapter):
    """Bitbucket API client."""
    
    def __init__(self, config: BitbucketConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.token}",
            "Accept": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated request to Bitbucket API."""
        url = f"{self.config.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def _get_paginated(self, endpoint: str, **kwargs) -> List[Dict]:
        """Handle Bitbucket's paginated responses."""
        results = []
        url = f"{self.config.base_url}{endpoint}"
        
        while url:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            data = response.json()
            
            results.extend(data.get("values", []))
            url = data.get("next")  # Next page URL
        
        return results
    
    def get_repository(self, owner: str = None, repo: str = None) -> Dict:
        workspace = owner or self.config.workspace
        repo_slug = repo or self.config.repo_slug
        return self._request("GET", f"/repositories/{workspace}/{repo_slug}")
    
    def list_issues(self, state: str = "open", **filters) -> List[Dict]:
        params = {"state": state}
        params.update(filters)
        return self._get_paginated(
            f"/repositories/{self.config.workspace}/{self.config.repo_slug}/issues",
            params=params
        )
    
    def get_issue(self, issue_number: int) -> Dict:
        return self._request(
            "GET",
            f"/repositories/{self.config.workspace}/{self.config.repo_slug}/issues/{issue_number}"
        )
    
    def list_issue_comments(self, issue_number: int) -> List[Dict]:
        # Bitbucket uses a different endpoint for comments
        return self._get_paginated(
            f"/repositories/{self.config.workspace}/{self.config.repo_slug}/issues/{issue_number}/comments"
        )
    
    def create_comment(self, issue_number: int, body: str) -> Dict:
        return self._request(
            "POST",
            f"/repositories/{self.config.workspace}/{self.config.repo_slug}/issues/{issue_number}/comments",
            json={"content": {"raw": body}}
        )
    
    def get_file_content(self, path: str, ref: str = "master") -> str:
        result = self._request(
            "GET",
            f"/repositories/{self.config.workspace}/{self.config.repo_slug}/src/{ref}/{path}"
        )
        # Bitbucket returns content directly for file endpoints
        return result
    
    def get_directory_contents(self, path: str = "", ref: str = "master") -> List[Dict]:
        return self._request(
            "GET",
            f"/repositories/{self.config.workspace}/{self.config.repo_slug}/src/{ref}/{path}"
        ).get("values", [])
    
    def get_repo_tree(self, ref: str = "master", recursive: bool = True) -> List[Dict]:
        # Bitbucket doesn't have a direct tree endpoint, use source listing
        result = self._request(
            "GET",
            f"/repositories/{self.config.workspace}/{self.config.repo_slug}/src/{ref}/"
        )
        # Transform to GitHub-like format
        values = result.get("values", [])
        return [
            {
                "path": item.get("path"),
                "type": "blob" if item.get("type") == "commit_file" else "tree",
                "sha": item.get("commit", {}).get("hash", "")
            }
            for item in values
        ]
```

### 5.4 Checkliste: Migration GitHub → Bitbucket

#### Phase 1: Vorbereitung

- [ ] Bitbucket Workspace + Repository erstellen
- [ ] Code aus GitHub zu Bitbucket migrieren
- [ ] App Password in Bitbucket erstellen
- [ ] Test-Tickets in Bitbucket anlegen

#### Phase 2: Adapter-Entwicklung

- [ ] `BitbucketAdapter` Klasse implementieren
- [ ] `BaseGitAdapter` Interface erfüllen
- [ ] Unit-Tests für Bitbucket Adapter
- [ ] Integrationstests mit Bitbucket

#### Phase 3: Configuration

- [ ] `GIT_PROVIDER` Environment Variable hinzufügen
- [ ] Config-Validierung für Bitbucket
- [ ] Dokumentation aktualisieren

#### Phase 4: Deployment

- [ ] `.env` auf Bitbucket-Credentials umstellen
- [ ] Smoke-Tests durchführen
- [ ] Paralleler Betrieb (optional)

### 5.5 Config-Switch Beispiel

```python
# src/config.py
import os
from typing import Union

from src.adapters.github.client import GitHubClient, GitHubConfig
from src.adapters.bitbucket.client import BitbucketAdapter, BitbucketConfig
from src.adapters.base import BaseGitAdapter


def create_git_adapter() -> BaseGitAdapter:
    """Factory function to create the appropriate Git adapter."""
    provider = os.getenv("GIT_PROVIDER", "github").lower()
    
    if provider == "github":
        config = GitHubConfig(
            token=os.getenv("GITHUB_TOKEN"),
            owner=os.getenv("GITHUB_OWNER"),
            repo=os.getenv("GITHUB_REPO")
        )
        return GitHubClient(config)
    
    elif provider == "bitbucket":
        config = BitbucketConfig(
            token=os.getenv("BITBUCKET_TOKEN"),
            workspace=os.getenv("BITBUCKET_WORKSPACE"),
            repo_slug=os.getenv("BITBUCKET_REPO")
        )
        return BitbucketAdapter(config)
    
    else:
        raise ValueError(f"Unknown Git provider: {provider}")
```

---

## 6. Zusammenfassung

### MVP Scope

| Feature | Status | Notes |
|---------|--------|-------|
| GitHub-Integration | ✅ | Lesen von Issues, Code, Comments |
| ORPA-Engine | ✅ | Observe → Reason → Plan → Act |
| Rückfragen-Workflow | ✅ | Automatische Fragen + Antworten |
| Kanban-Board | ✅ | SQLite-basiert, einfache UI |
| NO WRITE | ✅ | Keine Code-Änderungen im MVP |
| Bitbucket-Adapter | ⏳ | Zukunft: Einfacher Swap möglich |

### Geschätzte Kosten (MVP)

| Posten | Schätzung |
|--------|-----------|
| OpenRouter API (Testing) | $10-20/Monat |
| GitHub (kostenlos) | $0 |
| Hosting (optional) | $5-10/Monat |
| **Gesamt** | **~$15-30/Monat** |

### Nächste Schritte nach MVP

1. **WRITE-Operationen**: Code-Änderungen + Pull Requests
2. **Multi-Agent**: Tester-Agent hinzufügen
3. **Automatische Tests**: CI-Integration
4. **Bitbucket-Migration**: Produktions-Deployment
5. **Shopware-Integration**: Spezifische Shopware-Tools

---

*Dokument erstellt: 2024*
*Version: MVP Plan v1.0*
