# Gedächtnis- und Kontext-Management

## Übersicht

Das Multi-Agent System benötigt ein ausgeklügeltes Gedächtnismanagement, das:
- **Kunden-Isolation** garantiert (keine Datenlecks zwischen Kunden)
- **Mehrere Gedächtnis-Typen** unterstützt (Kurzzeit, Sitzung, Langzeit, Episodisch)
- **Kontext-basierte Entscheidungen** ermöglicht (Shopware-Version, PHP, Plugins)
- **Langfristiges Lernen** pro Kunde unterstützt

---

## 1. Gedächtnis-Architektur: 4-Schichten-Modell

### 1.1 Schichten-Übersicht

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
│  │    schritte     │  │  • Rate Limits  │  │                 │             │
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

### 1.2 Kunden-Isolation: Namespace-Strategie

Jeder Gedächtnis-Typ implementiert **Multi-Tenancy** durch Namespaces:

| Schicht | Isolation-Mechanismus | Beispiel-Key |
|---------|----------------------|--------------|
| Kurzzeit | Objekt-Attribut | `memory.customer_id = "alp-shopware"` |
| Sitzung | Redis Key-Prefix | `sess:{customer_id}:{session_id}:...` |
| Langzeit | ChromaDB Collection | `collection = "customer_{customer_id}"` |
| Episodisch | PostgreSQL Schema | `schema = "customer_{customer_id}"` |

```python
# Kunden-Isolations-Manager
class CustomerIsolation:
    """Zentrale Verwaltung der Kunden-Isolation über alle Gedächtnis-Schichten"""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self._validate_customer()
    
    @property
    def redis_prefix(self) -> str:
        """Redis-Key-Prefix für diesen Kunden"""
        return f"customer:{self.customer_id}"
    
    @property
    def chroma_collection(self) -> str:
        """ChromaDB Collection-Name"""
        # Sanitize für Collection-Namen (nur alphanumerisch + underscore)
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', self.customer_id)
        return f"customer_{safe_name}"
    
    @property
    def postgres_schema(self) -> str:
        """PostgreSQL Schema-Name"""
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', self.customer_id)
        return f"customer_{safe_name}"
    
    def validate_access(self, resource_customer_id: str) -> bool:
        """Prüft, ob Zugriff auf Ressource erlaubt ist"""
        if resource_customer_id != self.customer_id:
            raise CustomerIsolationViolation(
                f"Zugriff verweigert: Agent für '{self.customer_id}' "
                f"darf nicht auf Daten von '{resource_customer_id}' zugreifen"
            )
        return True
```

### 1.3 Datenspeicherung pro Kunde

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATENSPEICHERUNG PRO KUNDE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Kunde: alp-shopware                                                        │
│  ├── Redis:     customer:alp-shopware:* (alle Session-Keys)                │
│  ├── ChromaDB:  collection: "customer_alp_shopware"                        │
│  └── PostgreSQL: schema: "customer_alp_shopware"                           │
│       ├── conversations                                                    │
│       ├── tickets                                                          │
│       ├── code_patterns                                                    │
│       └── learning_episodes                                                │
│                                                                             │
│  Kunde: kraft-shopware                                                      │
│  ├── Redis:     customer:kraft-shopware:*                                  │
│  ├── ChromaDB:  collection: "customer_kraft_shopware"                      │
│  └── PostgreSQL: schema: "customer_kraft_shopware"                         │
│                                                                             │
│  Kunde: lupus                                                               │
│  ├── Redis:     customer:lupus:*                                           │
│  ├── ChromaDB:  collection: "customer_lupus"                               │
│  └── PostgreSQL: schema: "customer_lupus"                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Kontext-Layer: Hierarchische Struktur

### 2.1 Kontext-Hierarchie

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     KONTEXT-LAYER HIERARCHIE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Level 1: KUNDE (Customer)                                                  │
│  ├── Kunden-ID: alp-shopware                                                │
│  ├── Unternehmensdaten                                                      │
│  ├── Kontaktpersonen                                                        │
│  ├── SLA-Level                                                              │
│  └── Historische Lern-Muster                                                │
│         │                                                                   │
│         ▼                                                                   │
│  Level 2: PROJEKT (Project)                                                 │
│  ├── Projekt-ID: alp-shopware-prod                                          │
│  ├── Projekt-Typ: Production / Staging / Dev                                │
│  ├── Verantwortliche Agents                                                 │
│  └── Aktive Sprint/Zeitraum                                                 │
│         │                                                                   │
│         ▼                                                                   │
│  Level 3: REPOSITORY (Repository)                                           │
│  ├── Repo-URL: github.com/netgrade/alp-shopware                            │
│  ├── Primär-Sprache: PHP                                                    │
│  ├── Branch-Strategie: GitFlow                                              │
│  └── Letzter Commit / Status                                                │
│         │                                                                   │
│         ▼                                                                   │
│  Level 4: TECH-STACK (TechStack)                                            │
│  ├── Shopware-Version: 6.5.8.14                                             │
│  ├── PHP-Version: 8.1                                                       │
│  ├── Datenbank: MariaDB 10.4                                                │
│  ├── Cache: Redis                                                           │
│  └── Message-Queue: RabbitMQ                                                │
│         │                                                                   │
│         ▼                                                                   │
│  Level 5: PLUGINS & ERWEITERUNGEN                                           │
│  ├── Core-Plugins (Shopware)                                                │
│  ├── Netgrade-Plugins (eigene)                                              │
│  ├── Third-Party Plugins                                                    │
│  └── Custom-Entwicklungen                                                   │
│         │                                                                   │
│         ▼                                                                   │
│  Level 6: AKTUELLER KONTEXT (CurrentContext)                                │
│  ├── Aktives Ticket/Issue                                                   │
│  ├── Aktuelle Dateien (geöffnet)                                            │
│  ├── Konversations-Verlauf                                                  │
│  └── Temporäre Variablen                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Kontext-Initialisierung: Agent Start-Prozess

```python
class AgentContextInitializer:
    """Initialisiert den vollständigen Kontext beim Agent-Start"""
    
    async def initialize_context(self, agent_id: str, customer_id: str, 
                                  ticket_id: Optional[str] = None) -> AgentContext:
        """
        Initialisierungs-Reihenfolge (kritisch für Performance):
        
        1. Kunden-Kontext (aus PostgreSQL - cached)
        2. Projekt-Kontext (aus PostgreSQL - cached)  
        3. Tech-Stack (aus Config-DB)
        4. Plugin-Liste (aus ChromaDB + API-Cache)
        5. Ticket-Kontext (falls vorhanden)
        6. Historische Patterns (ChromaDB Embeddings)
        """
        
        context = AgentContext(agent_id=agent_id, customer_id=customer_id)
        
        # Schritt 1-3: Kritische Informationen (synchron laden)
        context.customer = await self._load_customer(customer_id)
        context.projects = await self._load_projects(customer_id)
        context.tech_stack = await self._load_tech_stack(customer_id)
        
        # Schritt 4: Plugin-Informationen (mit Fallback)
        context.plugins = await self._load_plugins(customer_id)
        
        # Schritt 5: Ticket-Kontext (falls spezifisches Ticket)
        if ticket_id:
            context.current_ticket = await self._load_ticket(ticket_id)
            context.ticket_history = await self._load_ticket_history(ticket_id)
        
        # Schritt 6: Historische Patterns (async im Hintergrund)
        asyncio.create_task(self._load_historical_patterns(context))
        
        return context
    
    async def _load_customer(self, customer_id: str) -> CustomerContext:
        """Lädt Kunden-Daten aus PostgreSQL"""
        query = """
            SELECT * FROM customers 
            WHERE customer_id = :customer_id
        """
        # Implementation...
    
    async def _load_tech_stack(self, customer_id: str) -> TechStack:
        """Lädt Tech-Stack aus zentraler Config"""
        query = """
            SELECT * FROM tech_stack_config 
            WHERE customer_id = :customer_id 
            AND is_active = true
            ORDER BY updated_at DESC 
            LIMIT 1
        """
        # Implementation...
```

### 2.3 Kritische Kontext-Informationen (MUST-HAVE)

| Kategorie | Information | Warum kritisch? | Quelle |
|-----------|-------------|-----------------|--------|
| **Identität** | `customer_id` | Isolation, Routing | JWT/Session |
| **Shopware** | Version (6.5.x / 6.6.x) | API-Unterschiede, Breaking Changes | Config-DB |
| **PHP** | Version (8.1 / 8.2 / 8.3) | Syntax, Features, Deprecations | Config-DB |
| **Datenbank** | MariaDB/MySQL + Version | SQL-Dialekt, Features | Config-DB |
| **Plugins** | Installierte + Versionen | Konflikte, Abhängigkeiten | ChromaDB + API |
| **Ticket** | aktuelles + Historie | Kontinuität, Dopplungen vermeiden | PostgreSQL |
| **Repository** | URL, Branch | Code-Zugriff, PR-Prozess | Config-DB |

### 2.4 Konkrete Kunden-Konfigurationen

```yaml
# customers/alp-shopware.yaml
customer:
  id: alp-shopware
  name: ALP GmbH
  
projects:
  - id: alp-shopware-prod
    name: ALP Production Shop
    repositories:
      - url: https://github.com/netgrade/alp-shopware
        branch: main
        
tech_stack:
  shopware:
    version: "6.5.8.14"
    channel: "stable"
  php:
    version: "8.1"
    extensions: [pdo_mysql, redis, gd, intl, mbstring]
  database:
    type: "mariadb"
    version: "10.4"
  cache:
    type: "redis"
    
plugins:
  core:
    - name: SwagLanguagePack
      version: "3.1.0"
  netgrade_custom:
    - name: AlpCustomTheme
      version: "2.3.1"
    - name: AlpProductExtension
      version: "1.5.0"
  third_party:
    - name: NetiNextEasyCoupon
      version: "5.2.0"
```

```yaml
# customers/kraft-shopware.yaml  
customer:
  id: kraft-shopware
  name: Kraft Handels GmbH
  
tech_stack:
  shopware:
    version: "6.7.6.2"  # Neuer!
    channel: "rc"
  php:
    version: "8.2"
  database:
    type: "mysql"
    version: "8.0"
    
plugins:
  third_party:
    - name: B2BSellersSuite
      version: "3.8.0"  # B2B-spezifisch
      critical: true
```

```yaml
# customers/lupus.yaml
customer:
  id: lupus
  name: Lupus Handels KG
  
tech_stack:
  shopware:
    version: "6.7.2.2"
  php:
    version: "8.2"
  database:
    type: "mariadb"
    version: "10.11"
    
plugins:
  store:
    - name: SwagPayPal
      version: "8.4.0"
    - name: SwagCmsExtensions
      version: "3.0.0"
```

---

## 3. Langzeitgedächtnis-Strategien

### 3.1 Embeddings für Code-Patterns

```python
class CodePatternMemory:
    """Speichert und retrieved Code-Patterns als Embeddings"""
    
    def __init__(self, chroma_client, customer_id: str):
        self.collection = chroma_client.get_or_create_collection(
            name=f"customer_{customer_id}_patterns"
        )
    
    def store_pattern(self, pattern: CodePattern):
        """
        Speichert ein erkanntes Code-Pattern:
        - Datei-Pfad
        - Code-Snippet  
        - Kontext (Shopware-Version, Plugin)
        - Lösungs-Qualität (hat es funktioniert?)
        """
        embedding = self._generate_embedding(pattern.code_snippet)
        
        self.collection.add(
            ids=[pattern.id],
            embeddings=[embedding],
            documents=[pattern.code_snippet],
            metadatas=[{
                "file_path": pattern.file_path,
                "pattern_type": pattern.type,  # "repository_decorator", "cart_processor", etc.
                "shopware_version": pattern.context.shopware_version,
                "success_rate": pattern.success_rate,
                "created_at": pattern.timestamp.isoformat(),
                "ticket_id": pattern.source_ticket
            }]
        )
    
    def find_similar_patterns(self, code_query: str, 
                              shopware_version: str,
                              limit: int = 5) -> List[CodePattern]:
        """
        Findet ähnliche Patterns für gegebenen Code.
        Filtert nach kompatibler Shopware-Version.
        """
        query_embedding = self._generate_embedding(code_query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit * 2,  # Mehr holen für Filter
            where={
                "$or": [
                    {"shopware_version": {"$eq": shopware_version}},
                    {"shopware_version": {"$eq": "all"}}  # Generische Patterns
                ]
            }
        )
        
        return self._rank_by_success_rate(results)[:limit]
```

### 3.2 Wiederverwendbare Lösungen pro Kunde

```python
class CustomerSolutionMemory:
    """
    Speichert erfolgreiche Lösungen pro Kunde.
    Wird aktualisiert basierend auf Ticket-Abschluss.
    """
    
    SOLUTION_TYPES = [
        "bugfix",           # Fehlerbehebung
        "feature",          # Neue Funktion
        "optimization",     # Performance-Verbesserung
        "configuration",    # Konfigurations-Änderung
        "migration",        # Migrations-Skript
    ]
    
    def store_solution(self, ticket: Ticket, solution: Solution):
        """
        Speichert eine erfolgreiche Lösung.
        
        Metadaten:
        - Problem-Beschreibung (Embedding)
        - Lösung (Code + Erklärung)
        - Kategorie/Tags
        - Betroffene Dateien
        - Shopware-Version
        - Zeitstempel
        - Agent (wer hat es gelöst?)
        """
        document = f"""
        Problem: {ticket.description}
        Symptome: {ticket.symptoms}
        Fehlermeldung: {ticket.error_message}
        
        Lösung: {solution.description}
        Code: {solution.code_changes}
        """
        
        self.collection.add(
            ids=[f"sol_{ticket.id}_{solution.id}"],
            documents=[document],
            metadatas=[{
                "ticket_id": ticket.id,
                "solution_type": solution.type,
                "affected_files": json.dumps(solution.affected_files),
                "shopware_version": ticket.context.shopware_version,
                "plugins": json.dumps(ticket.context.installed_plugins),
                "success_verified": solution.verified,
                "resolution_time_hours": solution.resolution_time.total_seconds() / 3600,
                "created_by_agent": solution.agent_id,
                "created_at": datetime.now().isoformat()
            }]
        )
    
    def find_applicable_solutions(self, current_ticket: Ticket) -> List[SolutionMatch]:
        """
        Findet ähnliche, bereits gelöste Probleme.
        Nutzt für schnellere Problem-Lösung.
        """
        query = f"{current_ticket.description} {current_ticket.error_message}"
        
        results = self.collection.query(
            query_texts=[query],
            n_results=10,
            where={
                "success_verified": True,
                "shopware_version": current_ticket.context.shopware_version
            }
        )
        
        return self._format_results(results)
```

### 3.3 Fehler-Historie (Episodisches Lernen)

```sql
-- Episodische Fehler-Tabelle
CREATE TABLE customer_alp_shopware.error_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(255) NOT NULL,
    
    -- Fehler-Details
    error_type VARCHAR(100),           -- "syntax", "runtime", "logic", "performance"
    error_message TEXT,
    error_stacktrace TEXT,
    severity VARCHAR(20),              -- "critical", "high", "medium", "low"
    
    -- Kontext zum Zeitpunkt des Fehlers
    shopware_version VARCHAR(20),
    php_version VARCHAR(10),
    executed_code TEXT,                -- Was wurde ausgeführt?
    affected_file VARCHAR(500),
    
    -- Root Cause (nach Analyse)
    root_cause_category VARCHAR(100),  -- "plugin_conflict", "version_incompatibility", "config_error"
    root_cause_analysis TEXT,
    
    -- Lösung
    resolution_strategy TEXT,          -- Wie wurde es behoben?
    prevention_measures TEXT,          -- Wie vermeiden?
    
    -- Metadaten
    occurred_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    created_by_agent VARCHAR(100),
    
    -- Vektor für semantische Suche
    error_embedding VECTOR(1536)       -- pgvector
);

-- Index für semantische Suche
CREATE INDEX idx_error_embedding ON customer_alp_shopware.error_episodes 
USING ivfflat (error_embedding vector_cosine_ops);

-- Index für häufige Abfragen
CREATE INDEX idx_error_type_version ON customer_alp_shopware.error_episodes(error_type, shopware_version);
CREATE INDEX idx_error_occurred_at ON customer_alp_shopware.error_episodes(occurred_at DESC);
```

### 3.4 Lern-Algorithmus: Feedback-Loop

```python
class ContinuousLearningEngine:
    """
    Aktualisiert das Langzeitgedächtnis basierend auf:
    - Ticket-Abschluss (erfolgreich / nicht erfolgreich)
    - Code-Review Feedback
    - Kunden-Feedback
    - System-Metriken (Performance, Fehlerrate)
    """
    
    def process_ticket_resolution(self, ticket: Ticket, outcome: ResolutionOutcome):
        """
        Wird aufgerufen wenn ein Ticket abgeschlossen wird.
        Aktualisiert alle relevanten Gedächtnis-Schichten.
        """
        
        if outcome.status == "success":
            # 1. Speichere als erfolgreiche Lösung
            self.solution_memory.store_solution(ticket, outcome.solution)
            
            # 2. Aktualisiere Code-Pattern Success-Rate
            for pattern in outcome.used_patterns:
                self.pattern_memory.increment_success(pattern.id)
            
            # 3. Update Agent-Belohnung (für RL)
            self.reward_model.update(ticket.agent_id, positive=True)
            
        elif outcome.status == "failure":
            # 1. Speichere Fehler-Episode
            self.error_memory.store_episode(ticket, outcome)
            
            # 2. Markiere verwendete Patterns als potenziell problematisch
            for pattern in outcome.used_patterns:
                self.pattern_memory.flag_for_review(pattern.id, ticket.id)
            
            # 3. Trigger Root Cause Analysis
            self.analyzer.schedule_deep_analysis(ticket)
    
    def generate_weekly_insights(self, customer_id: str) -> CustomerInsights:
        """
        Generiert wöchentliche Learning-Insights pro Kunde.
        """
        return CustomerInsights(
            recurring_issues=self._find_recurring_issues(customer_id),
            successful_patterns=self._top_patterns(customer_id),
            knowledge_gaps=self._identify_knowledge_gaps(customer_id),
            recommended_improvements=self._generate_recommendations(customer_id)
        )
```

---

## 4. Implementierungsdetails

### 4.1 ChromaDB Schema

```python
# chromadb_schema.py

from chromadb.config import Settings

CHROMA_SETTINGS = Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="/data/chroma",
    anonymized_telemetry=False
)

# Collections pro Kunde werden dynamisch erstellt
COLLECTIONS = {
    # Collection: {customer_id}_code_patterns
    "code_patterns": {
        "description": "Code-Patterns und Best Practices",
        "metadata_schema": {
            "file_path": "string",
            "pattern_type": "string",  # decorator, subscriber, service, etc.
            "language": "string",      # php, javascript, twig
            "shopware_version": "string",
            "success_rate": "float",
            "usage_count": "integer",
            "source_ticket": "string",
            "created_at": "datetime"
        },
        "embedding_model": "code-bert-multi",  # oder similar
        "distance_metric": "cosine"
    },
    
    # Collection: {customer_id}_solutions
    "solutions": {
        "description": "Erfolgreiche Problem-Lösungen",
        "metadata_schema": {
            "ticket_id": "string",
            "solution_type": "string",  # bugfix, feature, config
            "affected_files": "json",
            "shopware_version": "string",
            "plugins": "json",
            "success_verified": "boolean",
            "resolution_time_hours": "float",
            "created_by_agent": "string",
            "customer_rating": "integer"  # 1-5
        },
        "embedding_model": "text-embedding-3-large",
        "distance_metric": "cosine"
    },
    
    # Collection: {customer_id}_documentation
    "documentation": {
        "description": "Projekt-spezifische Dokumentation",
        "metadata_schema": {
            "doc_type": "string",       # api, architecture, process
            "topic": "string",
            "related_files": "json",
            "last_verified": "datetime",
            "verified_by": "string"
        },
        "embedding_model": "text-embedding-3-large",
        "distance_metric": "cosine"
    },
    
    # Collection: {customer_id}_conversations
    "conversations": {
        "description": "Zusammenfassungen vergangener Konversationen",
        "metadata_schema": {
            "ticket_id": "string",
            "conversation_type": "string",  # ticket, chat, email
            "participants": "json",
            "summary_type": "string",       # full, condensed, decision_only
            "key_decisions": "json",
            "outcome": "string"
        },
        "embedding_model": "text-embedding-3-large",
        "distance_metric": "cosine"
    }
}
```

### 4.2 PostgreSQL Schema für Episodisches Gedächtnis

```sql
-- ============================================
-- EPISODISCHES GEDÄCHTNIS: POSTGRESQL SCHEMA
-- ============================================

-- Extension für Vektor-Suche
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- SCHEMA: customer_{customer_id}
-- Wird pro Kunde dynamisch erstellt
-- ============================================

-- 1. KONVERSATIONEN (Chat-Verlauf)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id VARCHAR(255),
    conversation_id VARCHAR(255) NOT NULL,
    
    -- Nachricht
    message_role VARCHAR(20) NOT NULL,  -- "user", "assistant", "system", "tool"
    message_content TEXT NOT NULL,
    message_type VARCHAR(50),           -- "text", "code", "image", "file"
    
    -- Kontext zum Zeitpunkt der Nachricht
    agent_id VARCHAR(100) NOT NULL,
    agent_mode VARCHAR(50),             -- "observe", "reason", "plan", "act"
    context_snapshot JSONB,             -- Vollständiger Kontext (gehashed)
    
    -- Tool-Usage (falls applicable)
    tools_used JSONB,                   -- [{"tool": "git_diff", "result": "..."}]
    
    -- Metadaten
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    token_count INTEGER,
    
    -- Vektor für semantische Suche in Konversationen
    message_embedding VECTOR(1536)
);

CREATE INDEX idx_conversations_ticket ON conversations(ticket_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_conversations_embedding ON conversations USING ivfflat (message_embedding vector_cosine_ops);

-- 2. TICKETS (Erweiterte Ticket-Informationen)
CREATE TABLE tickets (
    id VARCHAR(255) PRIMARY KEY,
    external_id VARCHAR(255),           -- z.B. GitHub Issue #
    title VARCHAR(500) NOT NULL,
    description TEXT,
    
    -- Kategorisierung
    ticket_type VARCHAR(50),            -- "bug", "feature", "support", "task"
    priority VARCHAR(20),               -- "critical", "high", "medium", "low"
    status VARCHAR(30),                 -- "open", "in_progress", "resolved", "closed"
    
    -- Kontext
    shopware_version VARCHAR(20),
    affected_components JSONB,          -- ["checkout", "product", "cart"]
    affected_plugins JSONB,             -- ["SwagPayPal", "CustomPlugin"]
    
    -- Lösung
    resolution_summary TEXT,
    resolution_type VARCHAR(50),        -- "code_fix", "config_change", "education"
    files_changed JSONB,                -- ["src/Controller/OrderController.php"]
    
    -- Zeit
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    
    -- Agenten
    assigned_agent VARCHAR(100),
    contributing_agents JSONB,          -- ["agent_001", "agent_002"]
    
    -- Lern-Metriken
    resolution_attempts INTEGER DEFAULT 0,
    customer_satisfaction INTEGER,      -- 1-5
    
    -- Vektor
    description_embedding VECTOR(1536)
);

CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_type ON tickets(ticket_type);
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);
CREATE INDEX idx_tickets_embedding ON tickets USING ivfflat (description_embedding vector_cosine_ops);

-- 3. EPISODEN (Wichtige Ereignisse)
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_type VARCHAR(50) NOT NULL,  -- "error", "success", "decision", "milestone"
    
    -- Verknüpfung
    ticket_id VARCHAR(255) REFERENCES tickets(id),
    conversation_id VARCHAR(255),
    
    -- Inhalt
    episode_title VARCHAR(500) NOT NULL,
    episode_description TEXT,
    episode_data JSONB,                 -- Flexibles JSON für typ-spezifische Daten
    
    -- Kausalität (für "Warum ist das passiert?")
    preceding_episodes UUID[],          -- IDs vorheriger relevanter Episoden
    following_episodes UUID[],          -- IDs nachfolgender Episoden
    
    -- Kontext
    agent_id VARCHAR(100),
    shopware_version VARCHAR(20),
    environment VARCHAR(50),            -- "production", "staging", "local"
    
    -- Zeit
    occurred_at TIMESTAMP NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),
    
    -- Wichtigkeit (für Retention)
    importance_score FLOAT,             -- 0.0 - 1.0 (berechnet)
    retention_until TIMESTAMP,          -- Wann kann gelöscht werden?
    
    -- Vektor
    episode_embedding VECTOR(1536)
);

CREATE INDEX idx_episodes_ticket ON episodes(ticket_id);
CREATE INDEX idx_episodes_type ON episodes(episode_type);
CREATE INDEX idx_episodes_occurred ON episodes(occurred_at DESC);
CREATE INDEX idx_episodes_importance ON episodes(importance_score DESC);
CREATE INDEX idx_episodes_embedding ON episodes USING ivfflat (episode_embedding vector_cosine_ops);

-- 4. WORKFLOWS (Wiederkehrende Prozesse)
CREATE TABLE learned_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_name VARCHAR(200) NOT NULL,
    workflow_description TEXT,
    
    -- Trigger
    trigger_patterns JSONB NOT NULL,    -- [{"field": "error_message", "pattern": "..."}]
    trigger_embedding VECTOR(1536),
    
    -- Workflow-Schritte
    steps JSONB NOT NULL,               -- [{"step": 1, "action": "...", "tool": "..."}]
    
    -- Erfolgs-Metriken
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    avg_execution_time_minutes FLOAT,
    
    -- Kontext
    applicable_shopware_versions JSONB, -- ["6.5.x", "6.6.x"]
    applicable_customers JSONB,         -- Spezifisch oder ["all"]
    
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    
    -- Validierung
    verified_by VARCHAR(100),           -- Menschlicher Reviewer
    verified_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_workflows_trigger ON learned_workflows USING ivfflat (trigger_embedding vector_cosine_ops);

-- 5. KNOWLEDGE_GRAPH_NODES (Entitäten und Relationen)
CREATE TABLE knowledge_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_type VARCHAR(50) NOT NULL,     -- "file", "class", "function", "plugin", "concept"
    node_name VARCHAR(500) NOT NULL,
    node_description TEXT,
    
    -- Metadaten
    metadata JSONB,
    
    -- Vektor für semantische Ähnlichkeit
    node_embedding VECTOR(1536),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE knowledge_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_node UUID REFERENCES knowledge_nodes(id),
    to_node UUID REFERENCES knowledge_nodes(id),
    relation_type VARCHAR(100) NOT NULL, -- "imports", "extends", "uses", "depends_on", "solves"
    relation_strength FLOAT,             -- 0.0 - 1.0
    evidence JSONB,                      -- Tickets/Episoden die diese Relation belegen
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_knowledge_nodes_type ON knowledge_nodes(node_type);
CREATE INDEX idx_knowledge_nodes_embedding ON knowledge_nodes USING ivfflat (node_embedding vector_cosine_ops);
CREATE INDEX idx_knowledge_relations_from ON knowledge_relations(from_node);
CREATE INDEX idx_knowledge_relations_to ON knowledge_relations(to_node);
```

### 4.3 Redis Key-Struktur

```
# ============================================
# REDIS KEY-STRUKTUR
# Namespace: customer:{customer_id}:...
# ============================================

# 1. SESSION-MANAGEMENT
# --------------------
customer:{customer_id}:session:{session_id}:meta
  → { agent_id, started_at, last_activity, ticket_id }
  TTL: 24h

customer:{customer_id}:session:{session_id}:context
  → { current_state, active_tools, temp_variables }
  TTL: 24h

customer:{customer_id}:session:{session_id}:rate_limit:{tool_name}
  → ZSET (timestamps von API-Calls)
  TTL: 1h

# 2. CHAT-HISTORY (für aktive Konversationen)
# -------------------------------------------
customer:{customer_id}:chat:{chat_id}:messages
  → LIST [{role, content, timestamp, token_count}]
  TTL: 48h
  MAX-LEN: 100 (ältere → PostgreSQL)

customer:{customer_id}:chat:{chat_id}:summary
  → STRING (laufende Zusammenfassung für Kontext-Fenster)
  TTL: 48h

customer:{customer_id}:chat:{chat_id}:token_count
  → INTEGER (aktueller Token-Verbrauch)
  TTL: 48h

# 3. CACHE-LAYER
# --------------
# Tech-Stack Config (selten ändernd)
customer:{customer_id}:cache:tech_stack
  → HASH { shopware_version, php_version, db_type, ... }
  TTL: 1h

# Plugin-Liste (mittlere Änderungsrate)
customer:{customer_id}:cache:plugins
  → HASH { plugin_name → version }
  TTL: 15min

# Code-Patterns (Query-Cache)
customer:{customer_id}:cache:pattern:{pattern_hash}
  → STRING (ChromaDB Query Result)
  TTL: 5min

# Git-API Responses
customer:{customer_id}:cache:git:{cache_key}
  → STRING (API Response)
  TTL: 2min

# 4. ORPA-Zustand (Observe-Reason-Plan-Act)
# -----------------------------------------
customer:{customer_id}:orpa:{session_id}:current_phase
  → STRING ("observe" | "reason" | "plan" | "act")
  TTL: 1h

customer:{customer_id}:orpa:{session_id}:observations
  → LIST (gesammelte Beobachtungen)
  TTL: 1h

customer:{customer_id}:orpa:{session_id}:reasoning
  → STRING (Reasoning-Output)
  TTL: 1h

customer:{customer_id}:orpa:{session_id}:plan
  → LIST [{step_id, action, status, result}]
  TTL: 1h

# 5. TEMPORÄRE ARBEITSDATEN
# -------------------------
customer:{customer_id}:temp:{session_id}:{artifact_id}
  → Beliebige Daten (Datei-Inhalte, Diff-Outputs, etc.)
  TTL: 30min

# 6. LOCKING & KOORDINATION (für Multi-Agent)
# -------------------------------------------
customer:{customer_id}:lock:ticket:{ticket_id}
  → STRING { agent_id, acquired_at }
  TTL: 5min (mit Heartbeat-Verlängerung)

customer:{customer_id}:lock:file:{file_path_hash}
  → STRING { agent_id, operation }
  TTL: 2min

# 7. RATE LIMITING & QUOTAS
# -------------------------
customer:{customer_id}:quota:llm_tokens:{date}
  → INTEGER (verbrauchte Tokens heute)
  TTL: 48h

customer:{customer_id}:quota:api_calls:{service}:{date}
  → INTEGER (API Calls an externe Services)
  TTL: 48h

# 8. REAL-TIME EVENTS (Pub/Sub)
# -----------------------------
customer:{customer_id}:events:ticket_updates
  → STREAM (neue Ticket-Events)

customer:{customer_id}:events:agent_messages
  → STREAM (Agent-zu-Agent Kommunikation)
```

### 4.4 Redis Implementierungsbeispiel

```python
# redis_manager.py

import redis.asyncio as redis
from typing import Optional, Any
import json

class CustomerRedisManager:
    """
    Redis-Manager mit integrierter Kunden-Isolation.
    Alle Keys werden automatisch mit Customer-ID prefixed.
    """
    
    def __init__(self, redis_client: redis.Redis, customer_id: str):
        self.redis = redis_client
        self.customer_id = customer_id
        self.prefix = f"customer:{customer_id}"
    
    def _key(self, *parts: str) -> str:
        """Erstellt einen customer-isolierten Key"""
        return f"{self.prefix}:{':'.join(parts)}"
    
    # === Session Management ===
    
    async def create_session(self, session_id: str, agent_id: str, 
                             ticket_id: Optional[str] = None) -> dict:
        """Erstellt eine neue Agent-Session"""
        session_data = {
            "agent_id": agent_id,
            "ticket_id": ticket_id,
            "started_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        key = self._key("session", session_id, "meta")
        await self.redis.setex(
            key, 
            ttl=timedelta(hours=24),
            value=json.dumps(session_data)
        )
        return session_data
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Lädt Session-Metadaten"""
        key = self._key("session", session_id, "meta")
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def update_activity(self, session_id: str):
        """Aktualisiert letzte Aktivität"""
        key = self._key("session", session_id, "meta")
        await self.redis.expire(key, timedelta(hours=24))
    
    # === Chat History ===
    
    async def append_message(self, chat_id: str, role: str, content: str, 
                             token_count: int):
        """Fügt Nachricht zum Chat hinzu"""
        key = self._key("chat", chat_id, "messages")
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "token_count": token_count
        }
        
        # RPUSH + LTRIM für maxlen
        pipe = self.redis.pipeline()
        pipe.rpush(key, json.dumps(message))
        pipe.ltrim(key, -100, -1)  # Nur letzte 100 behalten
        pipe.expire(key, timedelta(hours=48))
        await pipe.execute()
        
        # Token-Count aktualisieren
        await self.redis.incrby(
            self._key("chat", chat_id, "token_count"),
            token_count
        )
    
    async def get_chat_history(self, chat_id: str, limit: int = 50) -> list:
        """Lädt Chat-Verlauf"""
        key = self._key("chat", chat_id, "messages")
        messages = await self.redis.lrange(key, -limit, -1)
        return [json.loads(m) for m in messages]
    
    # === Caching ===
    
    async def get_cached(self, cache_type: str, cache_key: str) -> Optional[Any]:
        """Generischer Cache-Getter"""
        key = self._key("cache", cache_type, cache_key)
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def set_cached(self, cache_type: str, cache_key: str, 
                         value: Any, ttl: timedelta):
        """Generischer Cache-Setter"""
        key = self._key("cache", cache_type, cache_key)
        await self.redis.setex(key, ttl, json.dumps(value))
    
    # === Distributed Locking ===
    
    async def acquire_lock(self, resource_type: str, resource_id: str,
                           agent_id: str, ttl: timedelta = timedelta(minutes=5)) -> bool:
        """Versucht Lock zu erwerben"""
        key = self._key("lock", resource_type, resource_id)
        lock_data = json.dumps({
            "agent_id": agent_id,
            "acquired_at": datetime.now().isoformat()
        })
        
        # NX = Nur setzen wenn nicht existiert
        acquired = await self.redis.set(key, lock_data, nx=True, ex=ttl)
        return acquired is not None
    
    async def release_lock(self, resource_type: str, resource_id: str, 
                           agent_id: str) -> bool:
        """Gibt Lock frei (nur wenn wir ihn besitzen)"""
        key = self._key("lock", resource_type, resource_id)
        
        # Lua-Script für atomare Check-and-Delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        lock_data = json.dumps({"agent_id": agent_id})
        result = await self.redis.eval(lua_script, 1, key, lock_data)
        return result == 1
    
    async def extend_lock(self, resource_type: str, resource_id: str,
                          agent_id: str, additional_ttl: timedelta) -> bool:
        """Verlängert Lock (Heartbeat)"""
        key = self._key("lock", resource_type, resource_id)
        
        current = await self.redis.get(key)
        if not current:
            return False
        
        data = json.loads(current)
        if data["agent_id"] != agent_id:
            return False
        
        await self.redis.expire(key, additional_ttl)
        return True
```

---

## 5. Zusammenfassung & Architektur-Diagramm

### 5.1 Vollständiges System-Diagramm

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-AGENT SYSTEM: GEDÄCHTNIS & KONTEXT                           │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│   │                              AGENT LAYER                                            │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │  │
│   │  │   Agent 1   │  │   Agent 2   │  │   Agent 3   │  │   Agent N   │                │  │
│   │  │ (Bugfixer)  │  │(Architect)  │  │  (Tester)   │  │  (Deployer) │                │  │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │  │
│   │         └─────────────────┴─────────────────┴─────────────────┘                     │  │
│   │                                    │                                                │  │
│   │                           ORPA Loop (Observe-Reason-Plan-Act)                      │  │
│   └────────────────────────────────────┼────────────────────────────────────────────────┘  │
│                                        │                                                    │
│                                        ▼                                                    │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│   │                         CONTEXT INITIALIZER                                         │  │
│   │   customer_id ──► CustomerContext ──► Projects ──► TechStack ──► Plugins           │  │
│   │   ticket_id ────► TicketContext ──► History ──► Related Solutions                  │  │
│   └────────────────────────────────────┼────────────────────────────────────────────────┘  │
│                                        │                                                    │
│           ┌────────────────────────────┼────────────────────────────┐                      │
│           │                            │                            │                      │
│           ▼                            ▼                            ▼                      │
│   ┌───────────────┐          ┌─────────────────┐          ┌─────────────────┐             │
│   │  KURZZEIT     │          │    SITZUNG      │          │    LANGZEIT     │             │
│   │  (In-Memory)  │          │    (Redis)      │          │   (ChromaDB)    │             │
│   │               │          │                 │          │                 │             │
│   │ • Active      │          │ • Chat History  │          │ • Code Patterns │             │
│   │   Context     │◄────────►│ • Session Data  │◄────────►│ • Solutions     │             │
│   │ • Reasoning   │          │ • Rate Limits   │          │ • Documentation │             │
│   │   Steps       │          │ • Locks         │          │ • Embeddings    │             │
│   │ • Tool State  │          │ • Cache         │          │                 │             │
│   └───────────────┘          └─────────────────┘          └─────────────────┘             │
│           │                                                            │                   │
│           │                    ┌───────────────────────────────────────┘                   │
│           │                    │                                                           │
│           │                    ▼                                                           │
│           │          ┌─────────────────────────────────────────────────────────┐            │
│           │          │         EPISODISCHES GEDÄCHTNIS (PostgreSQL)            │            │
│           │          │                                                           │            │
│           │          │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   │            │
│           └─────────►│  │ conversations │ │    tickets    │ │   episodes    │   │            │
│                      │  └───────────────┘ └───────────────┘ └───────────────┘   │            │
│                      │  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   │            │
│                      │  │ learned_work- │ │  knowledge_   │ │  error_       │   │            │
│                      │  │    flows      │ │    nodes      │ │  episodes     │   │            │
│                      │  └───────────────┘ └───────────────┘ └───────────────┘   │            │
│                      │                                                           │            │
│                      │  • Vollständige Ticket-Historie                           │            │
│                      │  • Zeitliche Abfolge & Kausalität                         │            │
│                      │  • Fehler- & Lern-Episoden                                │            │
│                      │  • Knowledge Graph                                        │            │
│                      └─────────────────────────────────────────────────────────┘            │
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
│   │                        KUNDEN-ISOLATION (Multi-Tenancy)                             │  │
│   │                                                                                     │  │
│   │   alp-shopware:  redis:customer:alp-shopware:*  chroma:customer_alp_shopware      │  │
│   │   kraft-shopware: redis:customer:kraft-shopware:* chroma:customer_kraft_shopware  │  │
│   │   lupus:          redis:customer:lupus:*          chroma:customer_lupus           │  │
│   │                                                                                     │  │
│   │   Keine Daten-Lecks zwischen Kunden garantiert!                                     │  │
│   └─────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Checkliste: Gedächtnis-Implementierung

| Komponente | Status | Priorität | Notizen |
|------------|--------|-----------|---------|
| **Kurzzeit** | ⬜ | Kritisch | In-Memory Dictionary pro Agent |
| **Redis-Sitzung** | ⬜ | Kritisch | 24-48h TTL, Key-Prefix pro Kunde |
| **ChromaDB-Setup** | ⬜ | Kritisch | Collections pro Kunde |
| **PostgreSQL-Schemas** | ⬜ | Kritisch | Dynamische Schema-Erstellung |
| **Kontext-Initializer** | ⬜ | Kritisch | Lade-Reihenfolge optimieren |
| **Kunden-Isolation** | ⬜ | Kritisch | Validierung auf allen Ebenen |
| **Code-Pattern-Embeddings** | ⬜ | Hoch | Model-Auswahl, Chunking |
| **Lösungs-Speicherung** | ⬜ | Hoch | Feedback-Loop |
| **Fehler-Episoden** | ⬜ | Mittel | Root-Cause-Analyse |
| **Knowledge Graph** | ⬜ | Niedrig | Long-term, Graph-RAG |

---

## 6. Nächste Schritte

1. **Datenbank-Setup**: ChromaDB + PostgreSQL mit pgvector installieren
2. **Redis-Schema implementieren**: Key-Struktur + TTL-Strategien
3. **Kontext-Initializer bauen**: Lade-Logik + Caching
4. **Kunden-Isolation testen**: Penetration-Testing für Data-Leaks
5. **Embedding-Pipeline**: Code-Parser + Chunking + Vectorisierung
6. **Feedback-Loop**: Ticket-Abschluss → Lern-Update
