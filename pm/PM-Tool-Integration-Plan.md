# PM-Tool Integration - Projektplan

> Teil des Multi-Agent KI-Mitarbeiter-Systems
> Stand: 20.02.2026

---

## Übersicht

| Phase | Zeitraum | Ziel | Status |
|-------|----------|------|--------|
| Phase 1 | Q1 2026 | Eigenes Kanban-Ticketboard (MVP) | Geplant |
| Phase 2 | Q2 2026 | Odoo-Integration | Optional |

---

## Phase 1: Eigenes Kanban-Ticketboard (MVP)

### 1.1 Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                     Agenten-System                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Planning    │  │ Execution   │  │ Communication Agent     │  │
│  │ Agent       │  │ Agent       │  │ (Rückfragen/Updates)    │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┼──────────────────────┘                │
│                          ▼                                       │
│              ┌─────────────────────┐                             │
│              │  PM-Tool Adapter    │                             │
│              │  (Abstract Layer)   │                             │
│              └──────────┬──────────┘                             │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PM-Tool Service                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ REST API     │  │ WebSocket    │  │ Event Bus (Redis)    │  │
│  │ (Agenten)    │  │ (Realtime)   │  │ (Async Processing)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         └─────────────────┼──────────────────────┘              │
│                           ▼                                     │
│              ┌─────────────────────────┐                        │
│              │    PostgreSQL           │                        │
│              │    (Tickets, Comments)  │                        │
│              └─────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Datenmodell

#### Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Customer   │       │    Ticket    │       │    Agent     │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄──────┤ id (PK)      │──────►│ id (PK)      │
│ name         │   1:n │ title        │  n:1  │ name         │
│ email        │       │ description  │       │ role         │
│ webhook_url  │       │ status       │       │ config       │
│ metadata     │       │ priority     │       └──────────────┘
│ created_at   │       │ customer_id  │
└──────────────┘       │ assignee_id  │◄────┐
                       │ metadata     │     │
                       │ created_at   │     │
                       │ updated_at   │     │
                       └──────────────┘     │
                               ▲             │
                               │             │
                       ┌──────────────┐      │
                       │   Comment    │      │
                       ├──────────────┤      │
                       │ id (PK)      │      │
                       │ ticket_id    │──────┘
                       │ author_type  │ (user/agent)
                       │ author_id    │
                       │ content      │
                       │ is_internal  │
                       │ created_at   │
                       └──────────────┘
```

#### SQL Schema (PostgreSQL)

```sql
-- Customers
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    webhook_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agents (interne Agenten-Registry)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL, -- 'planning', 'execution', 'communication'
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tickets
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'backlog', -- 'backlog', 'todo', 'in_progress', 'review', 'done'
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    
    -- Beziehungen
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    assignee_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    
    -- Repository-Kontext
    repository_id VARCHAR(255),
    branch_name VARCHAR(255),
    commit_sha VARCHAR(255),
    
    -- Agenten-Kontext
    context JSONB DEFAULT '{}', -- Agent-spezifischer Arbeitskontext
    estimated_effort INTEGER, -- in Minuten
    actual_effort INTEGER, -- in Minuten
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Comments (inkl. Rückfragen)
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    
    -- Polymorpher Autor
    author_type VARCHAR(20) NOT NULL CHECK (author_type IN ('agent', 'customer', 'system')),
    author_id UUID NOT NULL, -- Referenziert agents.id oder customers.id
    
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT false, -- Interne Notizen vs. Kundenkommunikation
    is_question BOOLEAN DEFAULT false, -- Markiert Rückfragen
    question_answered BOOLEAN DEFAULT NULL, -- NULL=keine Frage, TRUE=beantwortet, FALSE=offen
    
    -- Kundenbenachrichtigung
    customer_notified BOOLEAN DEFAULT false,
    notification_sent_at TIMESTAMP,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Status-History (Audit Trail)
CREATE TABLE status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by_type VARCHAR(20) NOT NULL,
    changed_by_id UUID NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indizes für Agenten-Queries
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_assignee ON tickets(assignee_id);
CREATE INDEX idx_tickets_customer ON tickets(customer_id);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_updated ON tickets(updated_at);
CREATE INDEX idx_comments_ticket ON comments(ticket_id);
CREATE INDEX idx_comments_question ON comments(is_question, question_answered) WHERE is_question = true;
```

### 1.3 Technologie-Stack

| Komponente | Technologie | Begründung |
|------------|-------------|------------|
| **Backend** | Python 3.11 + FastAPI | Async-native, OpenAPI-Generierung, KI-Ökosystem |
| **Datenbank** | PostgreSQL 16 | JSONB für flexible Metadata, zuverlässig |
| **Cache/Events** | Redis | Pub/Sub für Realtime-Updates, Caching |
| **Frontend** | React + TypeScript | Kanban-Board UI (optional für manuelle Steuerung) |
| **Container** | Docker + Docker Compose | Einfache Entwicklung & Deployment |
| **API-Docs** | OpenAPI 3.1 | Automatische Generierung für Agenten-Kontext |
| **Migrations** | Alembic | Datenbank-Schema-Versionierung |

### 1.4 API-Endpunkte (Agenten-fokussiert)

#### Core Ticket API

```yaml
openapi: 3.1.0
info:
  title: PM-Tool Agent API
  version: 1.0.0

paths:
  # ───────────────────────────────────────────────
  # TICKETS
  # ───────────────────────────────────────────────
  
  /api/v1/tickets:
    get:
      summary: Tickets für Agenten abrufen
      description: |
        Filterbare Liste aller Tickets. Agenten nutzen dies für:
        - "Gib mir alle offenen High-Priority Tickets"
        - "Zeige mir meine zugewiesenen Tickets"
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [backlog, todo, in_progress, review, done]
        - name: assignee_id
          in: query
          schema:
            type: string
            format: uuid
        - name: priority
          in: query
          schema:
            type: string
            enum: [low, medium, high, critical]
        - name: customer_id
          in: query
          schema:
            type: string
            format: uuid
        - name: search
          in: query
          description: Volltextsuche in Titel und Beschreibung
          schema:
            type: string
      responses:
        200:
          description: Liste von Tickets
          content:
            application/json:
              schema:
                type: object
                properties:
                  tickets:
                    type: array
                    items:
                      $ref: '#/components/schemas/Ticket'
                  total:
                    type: integer
    
    post:
      summary: Neues Ticket erstellen
      description: Wird typischerweise vom System oder Customer Webhook genutzt
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TicketCreate'
      responses:
        201:
          description: Ticket erstellt

  /api/v1/tickets/{ticket_id}:
    get:
      summary: Einzelnes Ticket mit allen Details
      description: |
        Liefert Ticket inkl. Comments, Customer-Info und Repository-Kontext.
        Wird vom Agenten beim Ticket-Start geladen.
      responses:
        200:
          description: Ticket-Details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TicketDetail'
    
    patch:
      summary: Ticket aktualisieren
      description: |
        Status-Updates, Zuweisungen, Priorität ändern
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TicketUpdate'

  # ───────────────────────────────────────────────
  # AGENTEN-AKTIONEN
  # ───────────────────────────────────────────────
  
  /api/v1/tickets/{ticket_id}/assign:
    post:
      summary: Ticket einem Agenten zuweisen
      description: |
        Ein Agent übernimmt ein Ticket. Setzt Status auf "in_progress".
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                agent_id:
                  type: string
                  format: uuid
                reason:
                  type: string
                  description: Warum übernimmt der Agent dieses Ticket?

  /api/v1/tickets/{ticket_id}/status:
    post:
      summary: Ticket-Status ändern
      description: |
        Status-Transition mit Validierung (z.B. done → in_progress erlaubt?)
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [status]
              properties:
                status:
                  type: string
                  enum: [backlog, todo, in_progress, review, done]
                reason:
                  type: string
                  description: Begründung für Status-Change

  # ───────────────────────────────────────────────
  # KOMMUNIKATION (Rückfragen & Updates)
  # ───────────────────────────────────────────────
  
  /api/v1/tickets/{ticket_id}/comments:
    get:
      summary: Alle Kommentare zu einem Ticket
      parameters:
        - name: include_internal
          in: query
          schema:
            type: boolean
            default: false
        - name: unanswered_only
          in: query
          description: Nur offene Rückfragen
          schema:
            type: boolean
            default: false
      responses:
        200:
          description: Liste von Kommentaren
    
    post:
      summary: Kommentar/Rückfrage hinzufügen
      description: |
        Agenten nutzen dies für:
        - Status-Updates ("Implementierung 80% fertig")
        - Rückfragen an Kunden ("Welche Farbe soll der Button haben?")
        - Interne Notizen
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [content, author_type, author_id]
              properties:
                content:
                  type: string
                  description: Markdown unterstützt
                author_type:
                  type: string
                  enum: [agent, customer, system]
                author_id:
                  type: string
                  format: uuid
                is_internal:
                  type: boolean
                  default: false
                is_question:
                  type: boolean
                  default: false
                  description: Ist dies eine Rückfrage?

  /api/v1/tickets/{ticket_id}/comments/{comment_id}/answer:
    post:
      summary: Rückfrage als beantwortet markieren
      description: |
        Wenn der Kunden antwortet, wird die Rückfrage geschlossen.
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                answer_content:
                  type: string
                  description: Antwort des Kunden

  # ───────────────────────────────────────────────
  # AGENTEN-KONTEXT
  # ───────────────────────────────────────────────
  
  /api/v1/agents/{agent_id}/tickets:
    get:
      summary: Alle Tickets eines Agenten
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [active, all, done]
      responses:
        200:
          description: Agent's Ticket-Übersicht

  /api/v1/agents/{agent_id}/workload:
    get:
      summary: Aktuelle Arbeitslast des Agenten
      description: |
        Gibt Anzahl Tickets pro Status und geschätzte Restzeit.
      responses:
        200:
          content:
            application/json:
              schema:
                type: object
                properties:
                  total_active:
                    type: integer
                  by_status:
                    type: object
                  estimated_remaining_minutes:
                    type: integer

components:
  schemas:
    Ticket:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
        description:
          type: string
        status:
          type: string
        priority:
          type: string
        customer:
          $ref: '#/components/schemas/CustomerBrief'
        assignee:
          $ref: '#/components/schemas/AgentBrief'
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
    
    TicketDetail:
      allOf:
        - $ref: '#/components/schemas/Ticket'
        - type: object
          properties:
            comments:
              type: array
              items:
                $ref: '#/components/schemas/Comment'
            status_history:
              type: array
              items:
                $ref: '#/components/schemas/StatusHistory'
            context:
              type: object
              description: Agent-spezifischer Arbeitskontext
    
    TicketCreate:
      type: object
      required: [title, customer_id]
      properties:
        title:
          type: string
        description:
          type: string
        priority:
          type: string
          default: medium
        customer_id:
          type: string
          format: uuid
        metadata:
          type: object
    
    TicketUpdate:
      type: object
      properties:
        title:
          type: string
        description:
          type: string
        status:
          type: string
        priority:
          type: string
        assignee_id:
          type: string
          format: uuid
        context:
          type: object
    
    Comment:
      type: object
      properties:
        id:
          type: string
        content:
          type: string
        author_type:
          type: string
        author_name:
          type: string
        is_internal:
          type: boolean
        is_question:
          type: boolean
        question_answered:
          type: boolean
        created_at:
          type: string
          format: date-time
    
    CustomerBrief:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
    
    AgentBrief:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        role:
          type: string
    
    StatusHistory:
      type: object
      properties:
        old_status:
          type: string
        new_status:
          type: string
        changed_by:
          type: string
        reason:
          type: string
        created_at:
          type: string
          format: date-time
```

### 1.5 Schnittstellen zum Agenten-System

#### Adapter Pattern

```python
# pm_tool/adapters/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class TicketInfo(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    customer: dict
    repository_context: Optional[dict]
    comments: List[dict]
    agent_context: dict  # Persistenter Kontext für Agenten

class PMToolAdapter(ABC):
    """Abstract Base für PM-Tool Integration"""
    
    @abstractmethod
    async def get_tickets(
        self, 
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[TicketInfo]:
        """Tickets für Agenten abrufen"""
        pass
    
    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> TicketInfo:
        """Einzelnes Ticket mit allen Details"""
        pass
    
    @abstractmethod
    async def update_status(
        self, 
        ticket_id: str, 
        status: str, 
        reason: Optional[str] = None
    ) -> bool:
        """Status-Update durchführen"""
        pass
    
    @abstractmethod
    async def assign_ticket(
        self, 
        ticket_id: str, 
        agent_id: str, 
        reason: Optional[str] = None
    ) -> bool:
        """Ticket zuweisen"""
        pass
    
    @abstractmethod
    async def add_comment(
        self,
        ticket_id: str,
        content: str,
        author_type: str = "agent",
        author_id: Optional[str] = None,
        is_internal: bool = False,
        is_question: bool = False
    ) -> dict:
        """Kommentar/Rückfrage hinzufügen"""
        pass
    
    @abstractmethod
    async def update_agent_context(
        self,
        ticket_id: str,
        context: dict
    ) -> bool:
        """Agent-spezifischen Kontext speichern"""
        pass
```

#### Konkrete Implementierung (Phase 1)

```python
# pm_tool/adapters/internal.py
import httpx
from .base import PMToolAdapter, TicketInfo

class InternalPMToolAdapter(PMToolAdapter):
    """Adapter für das eigene Kanban-Board"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"}
        )
    
    async def get_tickets(
        self, 
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[TicketInfo]:
        params = {}
        if status:
            params["status"] = status
        if assignee_id:
            params["assignee_id"] = assignee_id
        if priority:
            params["priority"] = priority
            
        response = await self.client.get("/api/v1/tickets", params=params)
        response.raise_for_status()
        
        return [TicketInfo(**ticket) for ticket in response.json()["tickets"]]
    
    async def get_ticket(self, ticket_id: str) -> TicketInfo:
        response = await self.client.get(f"/api/v1/tickets/{ticket_id}")
        response.raise_for_status()
        return TicketInfo(**response.json())
    
    async def update_status(
        self, 
        ticket_id: str, 
        status: str, 
        reason: Optional[str] = None
    ) -> bool:
        response = await self.client.post(
            f"/api/v1/tickets/{ticket_id}/status",
            json={"status": status, "reason": reason}
        )
        return response.status_code == 200
    
    async def add_comment(
        self,
        ticket_id: str,
        content: str,
        author_type: str = "agent",
        author_id: Optional[str] = None,
        is_internal: bool = False,
        is_question: bool = False
    ) -> dict:
        response = await self.client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            json={
                "content": content,
                "author_type": author_type,
                "author_id": author_id,
                "is_internal": is_internal,
                "is_question": is_question
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def update_agent_context(
        self,
        ticket_id: str,
        context: dict
    ) -> bool:
        response = await self.client.patch(
            f"/api/v1/tickets/{ticket_id}",
            json={"context": context}
        )
        return response.status_code == 200
```

### 1.6 Docker-Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  pm-tool-api:
    build:
      context: ./pm-tool
      dockerfile: Dockerfile
    container_name: pm-tool-api
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/pmtool
      - REDIS_URL=redis://redis:6379/0
      - API_KEY=${PM_TOOL_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./pm-tool:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8080 --reload

  postgres:
    image: postgres:16-alpine
    container_name: pm-tool-db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=pmtool
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: pm-tool-redis
    ports:
      - "6379:6379"

  pm-tool-frontend:
    build:
      context: ./pm-tool/frontend
      dockerfile: Dockerfile
    container_name: pm-tool-frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8080
    depends_on:
      - pm-tool-api

volumes:
  postgres_data:
```

---

## Phase 2: Odoo-Integration

### 2.1 Odoo API-Anbindung

#### Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                     Agenten-System                              │
│                          │                                      │
│              ┌───────────┴───────────┐                         │
│              │   PMToolAdapter       │                         │
│              │   (Interface)         │                         │
│              └───────────┬───────────┘                         │
│                          │                                      │
│          ┌───────────────┼───────────────┐                     │
│          ▼               ▼               ▼                     │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│   │  Internal  │  │   Odoo     │  │   Mock     │              │
│   │  Adapter   │  │  Adapter   │  │  Adapter   │              │
│   └─────┬──────┘  └─────┬──────┘  └────────────┘              │
└─────────┼───────────────┼──────────────────────────────────────┘
          │               │
          ▼               ▼
   ┌────────────┐  ┌────────────┐
   │  Internal  │  │    Odoo    │
   │   REST API │  │ XML-RPC/   │
   │            │  │ JSON-RPC   │
   └────────────┘  └─────┬──────┘
                         │
                         ▼
                  ┌────────────┐
                  │   Odoo     │
                  │  Server    │
                  │  Project   │
                  └────────────┘
```

#### Odoo Adapter Implementierung

```python
# pm_tool/adapters/odoo.py
import xmlrpc.client
from typing import List, Optional
from .base import PMToolAdapter, TicketInfo

class OdooPMToolAdapter(PMToolAdapter):
    """Adapter für Odoo Project Integration"""
    
    def __init__(
        self,
        url: str,
        database: str,
        username: str,
        api_key: str
    ):
        self.url = url
        self.db = database
        self.username = username
        self.api_key = api_key
        
        # Common endpoint für Auth
        self.common = xmlrpc.client.ServerProxy(
            f'{url}/xmlrpc/2/common'
        )
        # Object endpoint für CRUD
        self.models = xmlrpc.client.ServerProxy(
            f'{url}/xmlrpc/2/object'
        )
        
        self.uid = None
        self._authenticate()
    
    def _authenticate(self):
        """Odoo Authentifizierung"""
        self.uid = self.common.authenticate(
            self.db, 
            self.username, 
            self.api_key, 
            {}
        )
        if not self.uid:
            raise AuthenticationError("Odoo Login fehlgeschlagen")
    
    # ───────────────────────────────────────────────
    # Mapping: Odoo → Agenten-System
    # ───────────────────────────────────────────────
    
    ODOO_STATUS_MAP = {
        'backlog': 'Backlog',
        'todo': 'To Do',
        'in_progress': 'In Progress',
        'review': 'Waiting',
        'done': 'Done'
    }
    
    STATUS_REVERSE_MAP = {v: k for k, v in ODOO_STATUS_MAP.items()}
    
    def _odoo_task_to_ticket(self, task: dict) -> TicketInfo:
        """Konvertiert Odoo task → TicketInfo"""
        return TicketInfo(
            id=str(task['id']),
            title=task['name'],
            description=task.get('description', ''),
            status=self.STATUS_REVERSE_MAP.get(
                task.get('stage_id', [None, ''])[1], 
                'backlog'
            ),
            priority=self._map_priority(task.get('priority', '0')),
            customer=self._get_customer_info(task.get('partner_id')),
            repository_context=self._extract_repo_context(task),
            comments=self._get_comments(task['id']),
            agent_context=self._extract_agent_context(task)
        )
    
    def _map_priority(self, odoo_priority: str) -> str:
        """Odoo Priorität → System Priorität"""
        mapping = {'0': 'low', '1': 'medium', '2': 'high', '3': 'critical'}
        return mapping.get(odoo_priority, 'medium')
    
    def _extract_repo_context(self, task: dict) -> Optional[dict]:
        """Extrahiert Repository-Info aus Odoo Feldern"""
        # Odoo custom fields oder Description-Parsing
        metadata = task.get('x_metadata', '{}')
        if metadata:
            import json
            try:
                data = json.loads(metadata)
                return data.get('repository_context')
            except:
                pass
        return None
    
    def _extract_agent_context(self, task: dict) -> dict:
        """Extrahiert Agenten-Kontext aus Odoo"""
        context = {}
        if task.get('x_agent_context'):
            import json
            try:
                context = json.loads(task['x_agent_context'])
            except:
                pass
        return context
    
    # ───────────────────────────────────────────────
    # PMToolAdapter Implementation
    # ───────────────────────────────────────────────
    
    async def get_tickets(
        self, 
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[TicketInfo]:
        """Tasks aus Odoo Project laden"""
        domain = []
        
        if status:
            stage_name = self.ODOO_STATUS_MAP.get(status)
            if stage_name:
                # Suche Stage ID
                stage_ids = self.models.execute_kw(
                    self.db, self.uid, self.api_key,
                    'project.task.type', 'search',
                    [[['name', '=', stage_name]]]
                )
                if stage_ids:
                    domain.append(['stage_id', 'in', stage_ids])
        
        if assignee_id:
            # Agent → Odoo User Mapping
            domain.append(['user_ids', 'in', [int(assignee_id)]])
        
        tasks = self.models.execute_kw(
            self.db, self.uid, self.api_key,
            'project.task', 'search_read',
            [domain],
            {
                'fields': [
                    'id', 'name', 'description', 'stage_id',
                    'priority', 'partner_id', 'user_ids',
                    'x_metadata', 'x_agent_context'
                ]
            }
        )
        
        return [self._odoo_task_to_ticket(task) for task in tasks]
    
    async def get_ticket(self, ticket_id: str) -> TicketInfo:
        """Einzelnen Task laden"""
        tasks = self.models.execute_kw(
            self.db, self.uid, self.api_key,
            'project.task', 'search_read',
            [[['id', '=', int(ticket_id)]]],
            {
                'fields': [
                    'id', 'name', 'description', 'stage_id',
                    'priority', 'partner_id', 'user_ids',
                    'x_metadata', 'x_agent_context', 'message_ids'
                ]
            }
        )
        if not tasks:
            raise TicketNotFoundError(f"Task {ticket_id} nicht gefunden")
        return self._odoo_task_to_ticket(tasks[0])
    
    async def update_status(
        self, 
        ticket_id: str, 
        status: str, 
        reason: Optional[str] = None
    ) -> bool:
        """Status in Odoo aktualisieren"""
        stage_name = self.ODOO_STATUS_MAP.get(status)
        if not stage_name:
            return False
        
        # Stage ID finden
        stage_ids = self.models.execute_kw(
            self.db, self.uid, self.api_key,
            'project.task.type', 'search',
            [[['name', '=', stage_name]]]
        )
        
        if not stage_ids:
            return False
        
        # Update
        self.models.execute_kw(
            self.db, self.uid, self.api_key,
            'project.task', 'write',
            [[int(ticket_id)], {'stage_id': stage_ids[0]}]
        )
        
        # Log als Notiz
        if reason:
            self.models.execute_kw(
                self.db, self.uid, self.api_key,
                'project.task', 'message_post',
                [[int(ticket_id)]],
                {'body': f"Status-Update: {reason}"}
            )
        
        return True
    
    async def assign_ticket(
        self, 
        ticket_id: str, 
        agent_id: str, 
        reason: Optional[str] = None
    ) -> bool:
        """Task zuweisen"""
        self.models.execute_kw(
            self.db, self.uid, self.api_key,
            'project.task', 'write',
            [[int(ticket_id)], {'user_ids': [[6, 0, [int(agent_id)]]]}]
        )
        
        if reason:
            self.models.execute_kw(
                self.db, self.uid, self.api_key,
                'project.task', 'message_post',
                [[int(ticket_id)]],
                {'body': f"Zugewiesen: {reason}"}
            )
        return True
    
    async def add_comment(
        self,
        ticket_id: str,
        content: str,
        author_type: str = "agent",
        author_id: Optional[str] = None,
        is_internal: bool = False,
        is_question: bool = False
    ) -> dict:
        """Kommentar als Odoo Message hinzufügen"""
        # Odoo interne Notizen vs. Kunden-Emails
        message_type = 'comment' if not is_internal else 'notification'
        
        # Metadaten für Agent-System
        metadata = {
            'author_type': author_type,
            'is_question': is_question,
            'question_answered': None if not is_question else False
        }
        
        body = content
        if is_question:
            body = f"❓ **RÜCKFRAGE**\n\n{content}"
        
        message_id = self.models.execute_kw(
            self.db, self.uid, self.api_key,
            'project.task', 'message_post',
            [[int(ticket_id)]],
            {
                'body': body,
                'message_type': message_type,
                'x_agent_metadata': str(metadata)
            }
        )
        
        return {'id': message_id, 'created': True}
    
    async def update_agent_context(
        self,
        ticket_id: str,
        context: dict
    ) -> bool:
        """Agent-Kontext in Odoo speichern"""
        import json
        self.models.execute_kw(
            self.db, self.uid, self.api_key,
            'project.task', 'write',
            [[int(ticket_id)], {'x_agent_context': json.dumps(context)}]
        )
        return True
```

### 2.2 Mapping Odoo-Modelle → Agenten-Kontext

| Odoo Modell | Odoo Feld | Agenten-System | Nutzung |
|-------------|-----------|----------------|---------|
| `project.task` | `name` | `title` | Ticket-Titel |
| `project.task` | `description` | `description` | Beschreibung (HTML → Markdown) |
| `project.task` | `stage_id` | `status` | Status-Mapping |
| `project.task` | `priority` | `priority` | 0=low, 1=medium, 2=high, 3=critical |
| `project.task` | `partner_id` | `customer` | Kundenbezug |
| `project.task` | `user_ids` | `assignee_id` | Zugewiesene(r) Agent |
| `project.task` | `project_id` | - | Projekt-Zugehörigkeit |
| `project.task` | `x_metadata` | `repository_context` | Custom Field für Repo-Info |
| `project.task` | `x_agent_context` | `agent_context` | Custom Field für Agenten-Kontext |
| `mail.message` | `body` | `comments` | Kommentare/Notizen |
| `res.partner` | `name, email` | `customer` | Kundeninformationen |

### 2.3 Odoo Custom Fields (Installation)

```xml
<!-- odoo_custom_fields.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<odoo>
    <data>
        <!-- Feld für Repository/Metadaten -->
        <record id="project_task_metadata_field" model="ir.model.fields">
            <field name="name">x_metadata</field>
            <field name="model_id" ref="project.model_project_task"/>
            <field name="field_description">KI Metadata</field>
            <field name="ttype">text</field>
            <field name="help">JSON-Metadaten für KI-Agenten (Repository, Branch, etc.)</field>
        </record>

        <!-- Feld für Agenten-Kontext -->
        <record id="project_task_agent_context_field" model="ir.model.fields">
            <field name="name">x_agent_context</field>
            <field name="model_id" ref="project.model_project_task"/>
            <field name="field_description">Agent Context</field>
            <field name="ttype">text</field>
            <field name="help">Persistenter Kontext für KI-Agenten (Arbeitsstand, etc.)</field>
        </record>

        <!-- Feld für Rückfrage-Status in Messages -->
        <record id="mail_message_agent_metadata_field" model="ir.model.fields">
            <field name="name">x_agent_metadata</field>
            <field name="model_id" ref="mail.model_mail_message"/>
            <field name="field_description">Agent Metadata</field>
            <field name="ttype">text</field>
            <field name="help">Metadaten für Agenten-Kommunikation (Rückfragen, etc.)</field>
        </record>
    </data>
</odoo>
```

### 2.4 Migrationsstrategie: Internal → Odoo

```
┌─────────────────────────────────────────────────────────────────┐
│                    Migrations-Plan                              │
└─────────────────────────────────────────────────────────────────┘

Phase A: Vorbereitung (Vor Migration)
├── 1. Odoo Custom Fields installieren
├── 2. Stages in Odoo anlegen (Backlog, To Do, In Progress, Waiting, Done)
├── 3. Agenten als Odoo Users anlegen
├── 4. Customers aus Internal nach Odoo Partner migrieren
└── 5. Migration-Script testen

Phase B: Daten-Migration
├── 1. Tickets migrieren
│   ├── Title → name
│   ├── Description → description
│   ├── Status → stage_id (via Mapping)
│   ├── Priority → priority
│   ├── Customer → partner_id
│   ├── Assignee → user_ids
│   ├── Repository-Kontext → x_metadata
│   └── Agent-Context → x_agent_context
├── 2. Comments migrieren
│   ├── Content → body
│   ├── Author → author_id
│   └── Rückfrage-Status → x_agent_metadata
└── 3. Status-History als Notizen archivieren

Phase C: Switchover
├── 1. Config: PMToolAdapter = OdooPMToolAdapter
├── 2. Internal API read-only oder abschalten
├── 3. Webhook-URLs auf Odoo umstellen (falls externe Tickets)
└── 4. Rollback-Plan bereithalten

Phase D: Nachbereitung
├── 1. Internal DB als Backup behalten
├── 2. Monitoring: API-Response-Times
└── 3. Optimierung: Caching für Odoo-Queries
```

#### Migrations-Script

```python
# scripts/migrate_to_odoo.py
import asyncio
import json
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pm_tool.adapters.internal import InternalPMToolAdapter
from pm_tool.adapters.odoo import OdooPMToolAdapter

async def migrate_tickets():
    # Source: Internal DB
    internal = InternalPMToolAdapter(
        base_url="http://localhost:8080",
        api_key="internal_key"
    )
    
    # Target: Odoo
    odoo = OdooPMToolAdapter(
        url="https://odoo.company.com",
        database="production",
        username="api_user",
        api_key="odoo_api_key"
    )
    
    # Alle Tickets aus Internal laden
    tickets = await internal.get_tickets()
    
    for ticket in tickets:
        print(f"Migriere Ticket: {ticket.title}")
        
        # Customer finden oder erstellen
        partner_id = await find_or_create_partner(odoo, ticket.customer)
        
        # Agent mappen (Internal UUID → Odoo User ID)
        odoo_user_id = AGENT_MAPPING.get(ticket.assignee.get('id'))
        
        # In Odoo erstellen
        task_id = odoo.models.execute_kw(
            odoo.db, odoo.uid, odoo.api_key,
            'project.task', 'create',
            [{
                'name': ticket.title,
                'description': ticket.description,
                'project_id': DEFAULT_PROJECT_ID,
                'stage_id': map_stage(ticket.status),
                'priority': reverse_map_priority(ticket.priority),
                'partner_id': partner_id,
                'user_ids': [[6, 0, [odoo_user_id]]] if odoo_user_id else False,
                'x_metadata': json.dumps({
                    'repository_context': ticket.repository_context,
                    'migrated_from': 'internal',
                    'old_id': ticket.id
                }),
                'x_agent_context': json.dumps(ticket.agent_context)
            }]
        )
        
        # Comments migrieren
        for comment in ticket.comments:
            await migrate_comment(odoo, task_id, comment)
        
        print(f"  → Odoo Task ID: {task_id}")

async def find_or_create_partner(odoo, customer: dict) -> int:
    """Customer aus Internal nach Odoo Partner suchen/erstellen"""
    # Suche nach Email
    partner_ids = odoo.models.execute_kw(
        odoo.db, odoo.uid, odoo.api_key,
        'res.partner', 'search',
        [[['email', '=', customer['email']]]]
    )
    
    if partner_ids:
        return partner_ids[0]
    
    # Neu erstellen
    return odoo.models.execute_kw(
        odoo.db, odoo.uid, odoo.api_key,
        'res.partner', 'create',
        [{
            'name': customer['name'],
            'email': customer['email'],
            'is_company': False
        }]
    )

if __name__ == "__main__":
    asyncio.run(migrate_tickets())
```

---

## 3. Kommunikations-Workflow

### 3.1 Ticket-Lifecycle

```
┌─────────┐     ┌─────────┐     ┌─────────────┐     ┌─────────┐     ┌─────────┐
│ BACKLOG │────►│  TODO   │────►│ IN_PROGRESS │────►│ REVIEW  │────►│  DONE   │
└────┬────┘     └─────────┘     └──────┬──────┘     └────┬────┘     └─────────┘
     │                                 │                 │
     │    ┌────────────────────────────┘                 │
     │    │                                              │
     │    ▼                                              ▼
     │  ┌─────────────┐                         ┌─────────────┐
     │  │ Agent nimmt │                         │  Customer   │
     │  │  Ticket an  │                         │  Approval   │
     │  └─────────────┘                         └─────────────┘
     │
     ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    RÜCKFRAGE-MECHANISMUS                         │
  │                                                                  │
  │  Agent stellt Rückfrage → Status: "waiting_for_customer"        │
  │         │                                                        │
  │         ▼                                                        │
  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐        │
  │  │  Customer   │────►│  Webhook    │────►│  Ticket     │        │
  │  │  antwortet  │     │  benachr.   │     │  System     │        │
  │  └─────────────┘     └─────────────┘     └──────┬──────┘        │
  │                                                  │               │
  │                                                  ▼               │
  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐        │
  │  │ Agent setzt │◄────│  Kommentar  │◄────│  Rückfrage  │        │
  │  │  fort       │     │  hinzufügen │     │  beantwortet│        │
  │  └─────────────┘     └─────────────┘     └─────────────┘        │
  │                                                                  │
  └─────────────────────────────────────────────────────────────────┘
```

### 3.2 Status-Übergänge

| Von Status | Nach Status | Wer | Bedingung |
|------------|-------------|-----|-----------|
| `backlog` | `todo` | System/Agent | Ticket priorisiert |
| `todo` | `in_progress` | Agent | Agent übernimmt Ticket |
| `in_progress` | `review` | Agent | Arbeit abgeschlossen |
| `in_progress` | `waiting` | Agent | Rückfrage gestellt |
| `waiting` | `in_progress` | System | Kunde hat geantwortet |
| `review` | `done` | Customer | Freigabe erteilt |
| `review` | `in_progress` | Customer | Änderungen gewünscht |
| `done` | `in_progress` | Agent | Reopening (Bugfix) |

### 3.3 Rückfrage-Workflow (Detailliert)

```python
# workflows/question_workflow.py

class QuestionWorkflow:
    """Verwaltet Rückfragen zwischen Agenten und Kunden"""
    
    async def ask_question(
        self,
        ticket_id: str,
        question: str,
        agent_id: str,
        pm_tool: PMToolAdapter
    ) -> dict:
        """
        Agent stellt Rückfrage an Kunden
        """
        # 1. Kommentar als Rückfrage markieren
        comment = await pm_tool.add_comment(
            ticket_id=ticket_id,
            content=question,
            author_type="agent",
            author_id=agent_id,
            is_question=True
        )
        
        # 2. Status auf "waiting" setzen
        await pm_tool.update_status(
            ticket_id=ticket_id,
            status="waiting",
            reason=f"Rückfrage: {question[:50]}..."
        )
        
        # 3. Kunden benachrichtigen (Webhook/Email)
        await self._notify_customer(ticket_id, question)
        
        return {
            "comment_id": comment["id"],
            "status": "waiting",
            "notification_sent": True
        }
    
    async def receive_customer_response(
        self,
        ticket_id: str,
        response: str,
        customer_id: str,
        pm_tool: PMToolAdapter
    ) -> dict:
        """
        Kunde hat auf Rückfrage geantwortet
        """
        # 1. Antwort als Kommentar hinzufügen
        await pm_tool.add_comment(
            ticket_id=ticket_id,
            content=response,
            author_type="customer",
            author_id=customer_id
        )
        
        # 2. Offene Rückfragen schließen
        await self._close_open_questions(ticket_id, pm_tool)
        
        # 3. Status zurück auf "in_progress"
        await pm_tool.update_status(
            ticket_id=ticket_id,
            status="in_progress",
            reason="Kunde hat Rückfrage beantwortet"
        )
        
        # 4. Agenten benachrichtigen (Event/EventQueue)
        await self._notify_agent_available(ticket_id)
        
        return {
            "ticket_id": ticket_id,
            "new_status": "in_progress",
            "agent_notified": True
        }
    
    async def _close_open_questions(
        self, 
        ticket_id: str, 
        pm_tool: PMToolAdapter
    ):
        """Markiert alle offenen Rückfragen als beantwortet"""
        # In Phase 1: Direkte DB-Query
        # In Phase 2: Odoo API
        pass
    
    async def _notify_customer(self, ticket_id: str, question: str):
        """Benachrichtigt Kunden via Webhook/Email"""
        # Implementation je nach Customer-Setup
        pass
    
    async def _notify_agent_available(self, ticket_id: str):
        """Benachrichtigt Agenten dass Ticket weiterbearbeitet werden kann"""
        # Pub/Sub oder Event-Queue
        pass
```

### 3.4 Agenten-Interaktions-Muster

```python
# Agenten nutzen den PMToolAdapter für alle Interaktionen

class ExecutionAgent:
    def __init__(self, pm_tool: PMToolAdapter, question_workflow: QuestionWorkflow):
        self.pm_tool = pm_tool
        self.question_workflow = question_workflow
    
    async def process_ticket(self, ticket_id: str):
        """Haupt-Workflow für Ticket-Bearbeitung"""
        
        # 1. Ticket laden
        ticket = await self.pm_tool.get_ticket(ticket_id)
        
        # 2. Zuweisen
        await self.pm_tool.assign_ticket(
            ticket_id=ticket_id,
            agent_id=self.agent_id,
            reason="Ticket-Analyse und Bearbeitung"
        )
        
        # 3. Status: in_progress
        await self.pm_tool.update_status(
            ticket_id=ticket_id,
            status="in_progress"
        )
        
        # 4. Repository-Kontext laden
        repo_info = ticket.repository_context
        
        # 5. Bearbeitung...
        try:
            result = await self.execute_task(ticket)
            
            # 6a. Erfolg → Review
            await self.pm_tool.update_status(
                ticket_id=ticket_id,
                status="review",
                reason="Implementierung abgeschlossen"
            )
            
            await self.pm_tool.add_comment(
                ticket_id=ticket_id,
                content=self._format_completion_message(result),
                author_type="agent",
                author_id=self.agent_id
            )
            
        except UnclearRequirementsError as e:
            # 6b. Rückfrage nötig
            await self.question_workflow.ask_question(
                ticket_id=ticket_id,
                question=str(e),
                agent_id=self.agent_id,
                pm_tool=self.pm_tool
            )
            
        except ExecutionError as e:
            # 6c. Fehler → Interner Kommentar
            await self.pm_tool.add_comment(
                ticket_id=ticket_id,
                content=f"Fehler bei Ausführung: {str(e)}",
                author_type="agent",
                author_id=self.agent_id,
                is_internal=True
            )
    
    async def resume_after_answer(self, ticket_id: str):
        """Wird aufgerufen wenn Kunde auf Rückfrage geantwortet hat"""
        ticket = await self.pm_tool.get_ticket(ticket_id)
        
        # Letzte Antwort des Kunden holen
        last_customer_comment = [
            c for c in ticket.comments 
            if c.author_type == "customer"
        ][-1]
        
        # Mit Antwort fortfahren
        await self.process_ticket_with_context(
            ticket_id=ticket_id,
            additional_context=last_customer_comment.content
        )
```

### 3.5 Event-Flow Diagramm

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EVENT FLOW                                      │
└─────────────────────────────────────────────────────────────────────────┘

NEUES TICKET (via Webhook/Email)
│
▼
┌─────────────────┐
│ Ticket erstellt │──────────────────────────────────────────┐
│ Status: backlog │                                          │
└────────┬────────┘                                          │
         │                                                   │
         │ Webhook/Event                                     │
         ▼                                                   │
┌─────────────────┐                                          │
│ Planning Agent  │                                          │
│ analysiert und  │                                          │
│ priorisiert     │                                          │
└────────┬────────┘                                          │
         │                                                   │
         │ Status: todo                                      │
         ▼                                                   │
┌─────────────────┐     ┌─────────────────┐                 │
│ Execution Agent │◄────│ nimmt Ticket an │                 │
│ startet Arbeit  │     │ (oder assigned) │                 │
└────────┬────────┘     └─────────────────┘                 │
         │                                                   │
         │ Status: in_progress                               │
         │                                                   │
         ├───► [Arbeit erfolgreich] ─────────────────────► Review
         │                                                   │
         ├───► [Unklarheit] ─────────────────────────────► Rückfrage
         │                              │                    │
         │                              │ Status: waiting    │
         │                              │                    │
         │                              ▼                    │
         │                     ┌─────────────────┐          │
         │                     │ Customer        │          │
         │                     │ benachrichtigt  │──────────┘
         │                     └────────┬────────┘
         │                              │
         │◄─────────────────────────────│ Antwort eingegangen
         │                              │
         │ Status: in_progress          │
         │                              │
         ▼                              │
    [Weiterarbeit...]                   │
         │                              │
         ▼                              │
    [Review] ──────────────────────────►│ Customer Approval
         │                              │
         │ Status: done                 │
         ▼                              │
    ┌─────────┐                         │
    │ TICKET  │                         │
    │ CLOSED  │                         │
    └─────────┘◄────────────────────────┘
```

---

## 4. Zusammenfassung & Nächste Schritte

### 4.1 MVP Checkliste (Phase 1)

- [ ] PostgreSQL Schema erstellen
- [ ] FastAPI Backend mit CRUD-Endpunkten
- [ ] Docker Compose Setup
- [ ] PMToolAdapter Interface implementieren
- [ ] InternalPMToolAdapter fertigstellen
- [ ] Rückfrage-Workflow implementieren
- [ ] Webhook-Integration für Customer-Notifications
- [ ] Tests schreiben

### 4.2 Phase 2 Checkliste

- [ ] Odoo Custom Fields installieren
- [ ] OdooPMToolAdapter implementieren
- [ ] Status-Mapping validieren
- [ ] Migration-Script erstellen
- [ ] Test-Migration in Staging
- [ ] Rollback-Plan dokumentieren

### 4.3 Technische Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Odoo API Rate-Limits | Mittel | Hoch | Caching, Batching |
| Status-Mapping Fehler | Niedrig | Hoch | Unit-Tests, Validierung |
| Migration Datenverlust | Niedrig | Kritisch | Backup, Test-Runs |
| Webhook-Failures | Mittel | Mittel | Retry-Logik, Queue |

---

*Dokument erstellt am: 20.02.2026*
*Version: 1.0*
