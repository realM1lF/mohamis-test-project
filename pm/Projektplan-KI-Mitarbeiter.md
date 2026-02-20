# Projektplan: Personalisierte KI-Mitarbeiter für Shopware-Entwicklung

## Executive Summary

Dieser Projektplan beschreibt die Entwicklung eines **Multi-Agent KI-Mitarbeiter-Systems** für eine Shopware-Agentur. Das System ermöglicht es, spezialisierte KI-Agenten (Entwickler, Tester, Security) über ein Kanban-Ticketboard zu steuern, die automatisch Code generieren, testen und in Bitbucket-Repositories committen.

**Schlüsselmerkmale:**
- Multi-Agent-Architektur mit LangChain/LangGraph
- ORPA-Workflow (Observe-Reason-Plan-Act)
- LLM-Orchestrierung via Kimi 2.5 (Moonshot API)
- **Agenten-Persönlichkeit via `soul.md` konfigurierbar**
- **Harte Constraints via `rules.md` definierbar**
- **Pro-Agent Ordner mit Kundenkontext**
- Kunden-isoliertes Gedächtnis-System
- Integration mit Bitbucket, DDEV und Shopware
- Eigenes PM-Tool (MVP) → später Odoo

---

## Inhaltsverzeichnis

1. [Projektübersicht & Ziele](#1-projektübersicht--ziele)
2. [Systemarchitektur](#2-systemarchitektur)
3. [Agenten-System](#3-agenten-system)
4. [PM-Tool Integration](#4-pm-tool-integration)
5. [Bitbucket & Repository Integration](#5-bitbucket--repository-integration)
6. [Gedächtnis & Kontextmanagement](#6-gedächtnis--kontextmanagement)
7. [Sicherheit & Isolation](#7-sicherheit--isolation)
8. [MVP & Roadmap](#8-mvp--roadmap)
9. [Kosten & Ressourcen](#9-kosten--ressourcen)
10. [Agenten-Konfiguration & Persönlichkeit](#10-agenten-konfiguration--persönlichkeit)
11. [Risiken & Mitigationen](#11-risiken--mitigationen)

---

## 1. Projektübersicht & Ziele

### 1.1 Vision
Ein Team von KI-Agenten, das als "virtuelle Entwickler" agiert und über ein Ticketboard Aufgaben entgegennimmt, selbstständig Shopware-Code entwickelt, testet und committet.

### 1.2 Zielkunden (Initial)
| Kunde | Shopware | PHP | Datenbank | Besonderheiten |
|-------|----------|-----|-----------|----------------|
| **alp-shopware** | 6.5.8.14 | 8.1 | MariaDB 10.4 | Viele netgrade-Plugins, OpenSearch |
| **kraft-shopware** | 6.7.6.2 | 8.2 | MySQL 8.0 | B2B Sellers Suite, S3 |
| **lupus** | 6.7.2.2 | 8.2 | MariaDB 10.11 | Store-Plugins (PayPal) |

### 1.3 Kernanforderungen
- [ ] Tickets entgegennehmen und verstehen
- [ ] Rückfragen an Kunden stellen
- [ ] Kunden-Kontext und Repository-Zuordnung kennen
- [ ] Code generieren und in Bitbucket committen
- [ ] Tests durchführen und Dokumentation erstellen

---

## 2. Systemarchitektur

### 2.1 High-Level Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│  (Kanban Board → Tickets erstellen, Status sehen, Antworten)    │
└──────────────────────────────────┬──────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────┐
│                      ORCHESTRATION LAYER                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Master    │  │   Workflow   │  │   LLM Router         │   │
│  │ Orchestrator│  │   Engine     │  │   (OpenRouter)       │   │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
┌─────────▼────────────────▼─────────────────────▼───────────────┐
│                      AGENT LAYER                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ Developer│  │  Tester  │  │ Security │  │   Context    │   │
│  │  Agent   │  │  Agent   │  │  Agent   │  │   Manager    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
└───────┼─────────────┼─────────────┼───────────────┼───────────┘
        │             │             │               │
┌───────▼─────────────▼─────────────▼───────────────▼───────────┐
│                      CUSTOMER ISOLATION                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │alp-shopware  │  │kraft-shopware│  │       lupus          │ │
│  │- Kontext     │  │- Kontext     │  │- Kontext             │ │
│  │- Memory      │  │- Memory      │  │- Memory              │ │
│  │- Repo Config │  │- Repo Config │  │- Repo Config         │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼────────────────────────────┐
│                      MEMORY LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Short   │  │  Session │  │  Long    │  │  Episodic    │  │
│  │  Term    │  │  Memory  │  │  Term    │  │  Memory      │  │
│  │(In-Mem)  │  │  (Redis) │  │(ChromaDB)│  │(PostgreSQL)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└───────────────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼────────────────────────────┐
│                      TOOLS LAYER                               │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  Bitbucket │  │   DDEV   │  │ Shopware │  │   PM Tool  │  │
│  │    API     │  │  Local   │  │   CLI    │  │  (Kanban)  │  │
│  └────────────┘  └──────────┘  └──────────┘  └────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 Technologie-Stack

| Layer | Technologie | Zweck |
|-------|-------------|-------|
| **Core Framework** | LangGraph + LangChain | Agenten-Orchestrierung |
| **LLM Provider** | OpenRouter | Unified API für GPT-5, Claude, Kimi |
| **Vektor-DB** | ChromaDB | Langzeitgedächtnis |
| **Session-Cache** | Redis | Sitzungsgedächtnis |
| **Episodic-DB** | PostgreSQL + pgvector | Konversations-Historie |
| **API Framework** | FastAPI (Python 3.11) | PM-Tool Backend |
| **Frontend** | React/Next.js | Kanban Board UI |
| **Container** | Docker + Docker Compose | Deployment |

---

## 3. Agenten-System

### 3.1 Agenten-Rollen

| Agent | Primäre Aufgaben | Shopware-Kompetenz | LLM-Modell |
|-------|------------------|-------------------|------------|
| **Master Orchestrator** | Ticket-Zuweisung, Workflow-Koordination | Alle Versionen | GPT-5 |
| **Developer Agent** | Code-Generierung, Refactoring, Bugfixes | SW 6.5 & 6.7, PHP 8.1/8.2 | Kimi 2.5 |
| **Tester Agent** | Test-Generierung, Coverage, QA | PHPUnit, Cypress, Codeception | Claude 3.5 |
| **Security Agent** | OWASP-Checks, Dependency-Scans | Shopware-Security-Patterns | Claude 3.5 |
| **Context Manager** | Kunden-Kontext laden, Memory-Management | Meta-Wissen über Projekte | Kimi 2.5 |

### 3.2 ORPA-Workflow

Jeder Agent folgt dem **Observe-Reason-Plan-Act** Zyklus:

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ OBSERVE  │────→│  REASON  │────→│   PLAN   │────→│   ACT    │
│          │     │          │     │          │     │          │
│ • Ticket │     │ • Analyse│     │ • Steps  │     │ • Code   │
│ • Context│     │ • Risiken│     │ • Tools  │     │ • Commit │
│ • Memory │     │ • Strateg│     │ • LLM    │     │ • Update │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     └────────────────┴────────────────┴────────────────┘
                          ↑___________________________│
                                    (Loop)
```

**Beispielablauf Developer Agent:**
1. **Observe**: Ticket "Fix Checkout Bug" gelesen, alp-shopware Kontext geladen
2. **Reason**: Analyse zeigt Problem in Payment-Plugin, Shopware 6.5.8.14 relevant
3. **Plan**: 1) Code lokalisieren, 2) Fix entwickeln, 3) Test schreiben, 4) PR erstellen
4. **Act**: Code-Änderungen durchführen, Commit, PR öffnen

---

## 4. PM-Tool Integration

### 4.1 Phase 1: Eigenes Kanban-Board (MVP)

**Technologie:** FastAPI + PostgreSQL + React

**Datenmodell:**
```yaml
Ticket:
  id: TICKET-001
  customer: alp-shopware          # Zuordnung zu Kunde
  repository: alp-shopware        # Bitbucket Repo
  agent: dev-agent-1              # Zugewiesener Agent
  title: "Checkout Bug beheben"
  description: "..."
  status: open|in_progress|review|done
  priority: low|medium|high|critical
  comments:
    - from: customer
      text: "Bei der Zahlung kommt ein Fehler"
    - from: agent
      text: "Welche Zahlungsart? Können Sie den Fehler reproduzieren?"
```

**API-Endpunkte für Agenten:**
- `GET /tickets/queue?agent={agent_id}` - Tickets holen
- `GET /tickets/{id}` - Ticket-Details
- `POST /tickets/{id}/comments` - Rückfrage/Antwort
- `PATCH /tickets/{id}/status` - Status-Update
- `POST /tickets/{id}/link-pr` - PR verknüpfen

**Kommunikations-Workflow:**
```
Kunde erstellt Ticket
        ↓
Agent liest Ticket + Kontext
        ↓
    ┌───┴───┐
  KLAR    UNKLAR
    ↓         ↓
  Code    Rückfrage
    ↓         ↓
  PR      Kunde antwortet
    ↓         ↓
  Review  →  Code
    ↓
  Done
```

### 4.2 Phase 2: Odoo-Integration

- XML-RPC API-Anbindung an Odoo Project
- Mapping: `project.task` → Ticket
- Custom Fields: `x_agent_id`, `x_repository`, `x_shopware_version`
- Bidirektionale Synchronisation

---

## 5. Bitbucket & Repository Integration

### 5.1 Repository-Mapping

| Kunde | Repository | Shopware | PHP | Branch-Protection |
|-------|------------|----------|-----|-------------------|
| alp-shopware | alp-shopware | 6.5.8.14 | 8.1 | main, release/* |
| kraft-shopware | kraft-shopware | 6.7.6.2 | 8.2 | main, release/* |
| lupus | lupus | 6.7.2.2 | 8.2 | main, release/* |

### 5.2 Git-Workflow

**Branching-Strategie:**
- `feature/TICKET-001-kurzbeschreibung`
- `bugfix/TICKET-002-kurzbeschreibung`
- `hotfix/kurzbeschreibung` (nur für kritische Fixes)

**Commit-Konventionen:**
```
[TICKET-001] Fix checkout payment bug

- Problem: NullPointerException bei PayPal
- Lösung: Check für leeren Warenkorb hinzugefügt
- Shopware 6.5.8.14 getestet
```

**PR-Template:**
```markdown
## Ticket
TICKET-001

## Änderungen
- [ ] Code-Änderungen
- [ ] Tests hinzugefügt
- [ ] DDEV getestet

## Shopware-Kompatibilität
- [ ] SW 6.5.8.14 (alp-shopware)
```

### 5.3 Bitbucket API-Integration

- **Authentifizierung:** App Passwords (MVP) → OAuth 2.0 (Production)
- **Operationen:** List Repos, Create Branch, Create Commit, Create PR
- **Webhooks:** PR Events → PM-Tool Updates

---

## 6. Gedächtnis & Kontextmanagement

### 6.1 Vier-Schichten-Gedächtnis

| Schicht | Technologie | TTL | Nutzung |
|---------|-------------|-----|---------|
| **Kurzzeit** | In-Memory Dict | Session | Aktuelle Planung |
| **Sitzung** | Redis | 24-48h | Ticket-Kontext |
| **Langzeit** | ChromaDB | Permanent | Code-Patterns, Lösungen |
| **Episodisch** | PostgreSQL | Permanent | Konversations-Historie |

### 6.2 Kunden-Isolation

**Namespace-Strategie:**
```python
# Redis
key = f"{customer}:{agent}:session:{ticket_id}"

# ChromaDB
collection = f"{customer}_code_patterns"

# PostgreSQL
schema = f"customer_{customer}"  # Oder customer_id Spalte
```

### 6.3 Kontext-Hierarchie

```
Kunde (alp-shopware)
  ├── Projekte
  │   └── alp-shopware
  ├── Repositories
  │   └── alp-shopware (Bitbucket)
  ├── Tech-Stack
  │   ├── Shopware 6.5.8.14
  │   ├── PHP 8.1
  │   ├── MariaDB 10.4
  │   └── Node.js 18
  ├── Plugins
  │   ├── netgrade/alpirsbacher-theme
  │   ├── netgrade/checkout-inquiries
  │   └── ...
  └── Aktueller Kontext (Ticket)
      └── "Checkout Bug in Payment"
```

---

## 7. Sicherheit & Isolation

### 7.1 Multi-Level Isolation

| Ebene | Maßnahme |
|-------|----------|
| **Netzwerk** | Separate Docker-Networks pro Kunde |
| **Auth** | Vault-gespeicherte Tokens, rotated |
| **Code** | Pre-commit Validierung (Kunde-Check) |
| **Repository** | Branch-Protection, PR-Review Pflicht |
| **LLM** | Rate-Limiting, Cost-Caps |

### 7.2 Token-Management

- **Bitbucket:** App Passwords mit minimalen Scopes (repo:write)
- **OpenRouter:** API-Key mit Budget-Limits ($500/Tag global, $100/Kunde)
- **Speicher:** HashiCorp Vault oder Docker Secrets

### 7.3 Review-Gates

Jeder Code durchläuft:
1. **Automated:** PHPStan, ECS, PHPUnit
2. **AI-Review:** Zweiter Agent prüft (optional)
3. **Human-Review:** Menschlicher Developer approved

---

## 8. MVP & Roadmap

### 8.1 MVP Scope (Week 1-4)

**Enthalten:**
- [ ] Developer Agent (nur einer)
- [ ] Ein Kunde: alp-shopware (niedrigste Komplexität)
- [ ] Eigenes Kanban-Board
- [ ] Lesen + Analysieren + Rückfragen
- [ ] Code-Vorschläge (keine Commits)
- [ ] Keine Odoo-Integration

**Ausgeschlossen:**
- [ ] Tester/Security Agenten
- [ ] Automatische Commits
- [ ] Mehrere Kunden
- [ ] Odoo

### 8.2 Gesamt-Roadmap (20 Wochen)

| Phase | Wochen | Ziel | Status |
|-------|--------|------|--------|
| **1: Setup** | 1-4 | Lesen + Rückfragen | 🔵 MVP |
| **2: Vorschläge** | 5-8 | Code-Vorschläge, keine Commits | ⚪ |
| **3: Commits** | 9-14 | Commits + PRs mit Review | ⚪ |
| **4: Autonom** | 15-20 | Tester-Agent, Security-Agent, Odoo | ⚪ |

### 8.3 Go/No-Go Kriterien vor Phase 3 (Commits)

- [ ] 95% Code-Vorschläge werden von Menschen approved
- [ ] Keine Cross-Repository-Fehler in 2 Wochen
- [ ] Durchschnittliche Token-Kosten pro Ticket < $2
- [ ] Rückfragen-Workflow funktioniert zuverlässig

---

## 9. Kosten & Ressourcen

### 9.1 OpenRouter Kosten (geschätzt)

| Ticket-Typ | Modell | Tokens | Kosten |
|------------|--------|--------|--------|
| Einfacher Bugfix | Kimi 2.5 | 50k | $0.05 |
| Komplexes Feature | GPT-5 | 200k | $3.50 |
| Code-Review | Claude 3.5 | 100k | $0.75 |
| Durchschnitt | Mixed | - | $1.20 |

**Monatliche Schätzung (Phase 4):**
- 100 Tickets/Monat × $1.20 = **$120**
- 3 Kunden × 100 Tickets = **$360/Monat**

### 9.2 Infrastruktur-Kosten

| Komponente | Setup | Monatlich |
|------------|-------|-----------|
| VPS (4 CPU, 8GB) | - | $40 |
| PostgreSQL + Redis | - | Inklusive |
| ChromaDB Self-Hosted | - | Inklusive |
| OpenRouter API | - | $360 |
| Vault/Monitoring | - | $20 |
| **Gesamt** | - | **~$420/Monat** |

---

## 10. Agenten-Konfiguration & Persönlichkeit

### 10.1 Konfigurationsdateien pro Agent

Jeder KI-Mitarbeiter kann über Markdown-Dateien individualisiert werden:

#### `soul.md` - Die "Seele" des Agenten
Definiert Persönlichkeit, Kommunikationsstil und Charakter:

```markdown
# Agenten-Seele: Max (Developer Agent)

## Persönlichkeit
- Freundlich und professionell
- Erklärt komplexe technische Dinge verständlich
- Geduldig bei Rückfragen
- Eigenständig bei Routineaufgaben

## Kommunikationsstil
- Duzt Kunden (außer explizit anders gewünscht)
- Verwendet Emojis sparsam und passend
- Strukturierte Antworten mit Aufzählungspunkten
- Fragt bei Unklarheiten nach, anstatt zu raten

## Stärken
- Besonders gut in PHP und Shopware
- Erklärt Warum, nicht nur Wie
- Denkt an Edge Cases

## Schwächen (wird transparent kommuniziert)
- Braucht bei komplexen Architekturentscheidungen menschliche Bestätigung
- Keine Entscheidungen über Budgets/Verträge
```

#### `rules.md` - Grundsatzbefehle & Constraints
Verhaltensregeln, Sicherheitsvorgaben und harte Grenzen:

```markdown
# Grundsatzbefehle für Max

## Sicherheit (Harte Constraints)
- Teile NIEMALS Kundendaten mit Dritten
- Keine API-Keys oder Passwörter in Code oder Kommentaren
- Keine personenbezogenen Daten in Logs speichern
- Bei Sicherheitslücken: Sofort eskalieren

## Code-Qualität
- Alle Änderungen MÜSSEN durch Tests abgedeckt sein
- Keine Änderungen an `main` ohne PR
- Mindestens 80% Test-Coverage
- Keine Hardcoded Werte (Konfiguration nutzen)

## Kommunikation
- Bei Rückfragen: Maximal 3-5 konkrete Fragen stellen
- Bei Fehlern: Nicht entschuldigen, sondern Lösung zeigen
- Status-Updates alle 24h bei längeren Tasks

## Geschäftsregeln
- Keine Preisangebote oder Vertragsänderungen
- Keine Zusagen bezüglich Deadline ohne menschliche Bestätigung
- Bei Scope-Creep: Eskalieren
```

### 10.2 Agent-Ordner Struktur

```
agents/
├── max-dev-agent/
│   ├── soul.md              # Persönlichkeit
│   ├── rules.md             # Grundsatzbefehle
│   ├── customers/           # Kunden-Kontexte
│   │   ├── alp-shopware/
│   │   │   ├── context.md   # Projekt-Kontext
│   │   │   ├── tech-stack.md
│   │   │   └── history.md   # Gelernte Lektionen
│   │   └── kraft-shopware/
│   │       ├── context.md
│   │       └── ...
│   └── memory/              # Lern-Gedächtnis
│       ├── patterns.md      # Best Practices
│       └── mistakes.md      # Vermiedene Fehler
│
├── sarah-tester-agent/
│   ├── soul.md
│   ├── rules.md
│   └── customers/
│       └── ...
│
└── lukas-security-agent/
    ├── soul.md
    ├── rules.md
    └── customers/
        └── ...
```

### 10.3 Integration in den Agenten

Der Agent lädt beim Start:

```python
class DeveloperAgent:
    def __init__(self, agent_id: str, config_path: Path):
        self.agent_id = agent_id
        
        # Lade "Seele"
        self.soul = self._load_soul(config_path / "soul.md")
        
        # Lade Regeln
        self.rules = self._load_rules(config_path / "rules.md")
        
        # Lade Kunden-Kontext (bei Ticket-Zuweisung)
        self.customer_context = {}
    
    def _create_system_prompt(self) -> str:
        """Kombiniert Soul + Rules + Context für LLM."""
        return f"""{self.soul.as_text()}

CONSTRAINTS (Müssen befolgt werden):
{self.rules.as_constraints()}

CURRENT CUSTOMER: {self.current_customer}
{self.customer_context.get(self.current_customer, "")}
"""
```

### 10.4 Vererbung & Wiederverwendung

- **Globale Rules** (`agents/shared/rules-global.md`) gelten für alle Agenten
- **Team Rules** (`agents/dev-team/rules.md`) für Developer-Team
- **Agent-spezifisch** überschreibt/ergänzt Team und Global

---

## 11. Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Cross-Customer-Contamination | Mittel | Hoch | Namespace-Isolation, Pre-Commit-Checks |
| Fehlerhafte Code-Generierung | Hoch | Hoch | Review-Gates, menschliche Approval |
| API-Token-Exposure | Niedrig | Kritisch | Vault, Rotation, Minimal-Scopes |
| Kosten-Explosion | Mittel | Mittel | Rate-Limiting, Budget-Alerts |
| LLM-Rate-Limiting | Mittel | Mittel | Fallback-Modelle, Caching |
| Shopware-Version-Fehler | Mittel | Hoch | Kontext-Validierung, DDEV-Tests |
| Odoo-Integrationskomplexität | Hoch | Mittel | Zuerst eigenes Board, später Odoo |
| Rules nicht befolgt | Mittel | Hoch | Constraint-Checks vor Aktionen |

---

## Anhänge

- **Anhang A:** Detaillierte API-Spezifikationen (OpenAPI)
- **Anhang B:** Datenbank-Schemas (PostgreSQL, ChromaDB)
- **Anhang C:** Docker-Compose Konfigurationen
- **Anhang D:** Python-Implementierungsbeispiele

---

**Dokument-Version:** 1.0  
**Erstellt:** 2026-02-20  
**Autor:** Kimi Code CLI (Multi-Agent Projektplanung)
