# Sicherheits- und MVP-Planung

> **Projekt:** Multi-Agent KI-Mitarbeiter-System  
> **Stand:** 20.02.2026  
> **Kontext:** Produktiv-Code-Änderungen in Kundenprojekten (Hohes Risiko)

---

## 1. Sicherheitsarchitektur

### 1.1 Kunden-Isolation auf Code-Ebene

Die strikte Trennung der Kunden ist **kritisch**, da Cross-Customer-Contamination rechtliche Konsequenzen haben kann.

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUNDEN-ISOLATION-LAYERS                       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Repository-Level    │  SSH-Keys pro Kunde              │
│  Layer 3: Container-Level     │  Docker-Namespaces               │
│  Layer 2: Prozess-Level       │  Linux-User-Isolation            │
│  Layer 1: Datenbank-Level     │  PostgreSQL-Schemas              │
│  Layer 0: Netzwerk-Level      │  Firewall-Regeln                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Isolation-Strategie

| Ebene | Maßnahme | Implementierung | Validierung |
|-------|----------|-----------------|-------------|
| **Netzwerk** | Kein Inter-Kunden-Traffic | iptables/nftables | Ping-Test blockiert |
| **Filesystem** | Separate Mount-Namespaces | Docker Volumes | `find` über Kunden-Grenzen |
| **Prozess** | UID/GID pro Kunde | 10000+ Range | `ps aux` Check |
| **Git** | SSH-Config pro Kunde | `~/.ssh/config.d/` | `git remote -v` |
| **Memory** | Separate Redis-DBs | Redis DB 0-15 | `KEYS *` scoped |

#### Implementierungs-Checkliste

- [ ] **Repository-Struktur:**
  - [ ] `/data/customers/{customer-id}/repos/` für jeden Kunden
  - [ ] Git-Worktrees isoliert pro Repository
  - [ ] Keine symlinks über Kunden-Grenzen hinweg

- [ ] **SSH-Key-Management:**
  - [ ] Ein dedizierter SSH-Key pro Kunde
  - [ ] Keys in `/opt/ai-worker/keys/{customer-id}/`
  - [ ] Permissions: 600, Owner: ai-worker
  - [ ] Rotation alle 90 Tage

- [ ] **Container-Isolation:**
  - [ ] Docker-Compose pro Kunde
  - [ ] Separate Docker-Netzwerke
  - [ ] CPU/Memory-Limits pro Container

- [ ] **Validierungs-Skripte:**
  ```bash
  # Pre-Flight Check vor jedem Agent-Start
  ./scripts/validate-isolation.sh --customer={customer-id}
  ```

---

### 1.2 API-Token-Management

#### Bitbucket-Token-Strategie

| Token-Typ | Scope | Gültigkeit | Speicherort |
|-----------|-------|------------|-------------|
| **App-Passwort** | Repository-Read/Write | 90 Tage | HashiCorp Vault |
| **Workspace-Token** | PR-Create, Comment | 90 Tage | HashiCorp Vault |
| **Webhook-Secret** | Validation | Permanent | Environment Variable |

#### OpenRouter-Token-Strategie

```yaml
# Token-Rotation-Policy
openrouter:
  primary_token:
    scope: production
    limit: $500/month
    alerts: [80%, 90%, 95%, 100%]
  
  fallback_token:
    scope: emergency_only
    limit: $100/month
    requires_approval: true
```

#### Token-Sicherheits-Maßnahmen

- [ ] **Speicherung:**
  - [ ] HashiCorp Vault oder AWS Secrets Manager
  - [ ] Keine Tokens in Logs oder DB
  - [ ] Memory-only bei Runtime

- [ ] **Rotation:**
  - [ ] Automatische Rotation alle 90 Tage
  - [ ] Manual Rotation bei Verdacht auf Exposure
  - [ ] Audit-Log aller Token-Zugriffe

- [ ] **Überwachung:**
  - [ ] Real-time Alerts bei ungewöhnlichem Usage
  - [ ] Geo-IP-Prüfung für API-Calls
  - [ ] IP-Whitelist für Bitbucket-Zugriff

---

### 1.3 Rate-Limiting für LLM-Calls

#### Multi-Level Rate-Limiting

```
┌────────────────────────────────────────────────────────────┐
│  Level 1: Global (System)                                   │
│  → Max $500/Tag Gesamtkosten                               │
├────────────────────────────────────────────────────────────┤
│  Level 2: Per Customer                                      │
│  → Max $100/Tag pro Kunde                                  │
├────────────────────────────────────────────────────────────┤
│  Level 3: Per Agent                                         │
│  → Max 50 Calls/Stunde                                     │
├────────────────────────────────────────────────────────────┤
│  Level 4: Per Task                                          │
│  → Max $5 pro Ticket                                       │
└────────────────────────────────────────────────────────────┘
```

#### Rate-Limit-Konfiguration

| Limit-Typ | Wert | Aktion bei Überschreitung |
|-----------|------|---------------------------|
| **Kosten-Limit (Global)** | $500/Tag | Queue + Alert |
| **Kosten-Limit (Kunde)** | $100/Tag | Pause + Notification |
| **Request-Limit (Agent)** | 50/Std | Throttling (exponentiell) |
| **Token-Limit (Request)** | 100k Tokens | Chunking + Warnung |
| **Kosten-Limit (Ticket)** | $5 | Escalation an Mensch |

#### Circuit Breaker Pattern

```python
@circuit_breaker(
    failure_threshold=5,
    recovery_timeout=60,
    half_open_max_calls=3
)
async def llm_call_with_protection(prompt, context):
    # Implementierung mit Retry-Logik
    pass
```

---

### 1.4 Sandbox/Review-Prozess

#### Code-Ausführungs-Sandbox

| Umgebung | Zweck | Einschränkungen |
|----------|-------|-----------------|
| **Dry-Run** | Syntax-Check, Linting | Keine externen Calls |
| **Test-Sandbox** | Unit-Tests, Integration | Mocked externe Services |
| **Staging** | E2E-Tests, Review | Production-Daten (anonymisiert) |
| **Production** | Live-Deployment | Nur nach 2x Approval |

#### Review-Prozess-Workflow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Agent   │───→│  Draft   │───→│  Review  │───→│  Merge   │
│  Output  │    │  PR      │    │  Gate    │    │  (Mensch)│
└──────────┘    └──────────┘    └──────────┘    └──────────┘
      │                              ↑
      │         ┌──────────┐         │
      └────────→│ Rückfrage│─────────┘
                │ (Agent)  │
                └──────────┘
```

#### Review-Gate-Kriterien

- [ ] **Automated Checks:**
  - [ ] Syntax-Validierung (PHP, JS, Python)
  - [ ] Linting (ESLint, PHP_CodeSniffer)
  - [ ] Security-Scan (Semgrep, Trivy)
  - [ ] Test-Coverage ≥ 80%

- [ ] **Manuelle Review-Pflicht bei:**
  - [ ] Änderungen an Kern-Modulen
  - [ ] Datenbank-Migrationen
  - [ ] API-Schnittstellen-Änderungen
  - [ ] Security-relevantem Code
  - [ ] Kosten > $5 an LLM-Calls

---

## 2. MVP-Definition

### 2.1 Was ist das Minimum, das funktioniert?

```
┌────────────────────────────────────────────────────────────────┐
│  MVP SCOPE = Lesen + Analysieren + Rückfragen (NO WRITE)       │
├────────────────────────────────────────────────────────────────┤
│  IN SCOPE:                                                     │
│  • Ticket aus Focalboard lesen                                 │
│  • Code-Repository analysieren                                 │
│  • Fragen an menschlichen PM stellen                           │
│  • Dokumentation der Analyse                                   │
├────────────────────────────────────────────────────────────────┤
│  OUT OF SCOPE (Phase 2+):                                      │
│  • Code-Änderungen                                             │
│  • Commits/Pull Requests                                       │
│  • Automatische Tests                                          │
│  • Deployment                                                  │
└────────────────────────────────────────────────────────────────┘
```

#### MVP-Feature-Checkliste

| Feature | MVP | Phase 2 | Phase 3 | Phase 4 |
|---------|-----|---------|---------|---------|
| Ticket lesen | ✅ | ✅ | ✅ | ✅ |
| Code analysieren | ✅ | ✅ | ✅ | ✅ |
| Rückfragen stellen | ✅ | ✅ | ✅ | ✅ |
| Code-Vorschläge erstellen | ❌ | ✅ | ✅ | ✅ |
| PRs erstellen | ❌ | ❌ | ✅ | ✅ |
| Automatisch committen | ❌ | ❌ | ❌ | ✅ |
| Autonom deployen | ❌ | ❌ | ❌ | ✅ |

### 2.2 Welcher Agent zuerst?

**Empfehlung: Nur Dev-Agent im MVP**

Begründung:
- Tester-Agent benötigt Dev-Agent Output als Input
- Security-Agent ist Overhead für lesenden Betrieb
- Dev-Agent kann bereits 80% der Ticket-Arten analysieren

```
MVP:         [Dev-Agent] ──→ Rückfragen ──→ Mensch
Phase 2:     [Dev-Agent] ──→ Code-Vorschlag ──→ Review
Phase 3:     [Dev-Agent] ──→ [Tester-Agent] ──→ PR ──→ Review
Phase 4:     [Dev-Agent] ──→ [Tester-Agent] ──→ [Security-Agent] ──→ Deploy
```

### 2.3 Welcher Kunde zuerst?

#### Optionen-Vergleich

| Kriterium | Alle 3 | Nur alp-shopware | Nur kraft-shopware | Nur lupus |
|-----------|--------|------------------|-------------------|-----------|
| **Setup-Aufwand** | 3x | 1x | 1x | 1x |
| **Isolierung-Test** | ✅ Vollständig | ⚠️ Teilweise | ⚠️ Teilweise | ⚠️ Teilweise |
| **Fehler-Auswirkung** | Hoch | Niedrig | Niedrig | Niedrig |
| **Lernkurve** | Steil | Flach | Flach | Flach |
| **Kosten (MVP)** | 3x | 1x | 1x | 1x |

#### Empfehlung: alp-shopware zuerst

**Begründung:**
1. Bestehende CI/CD-Infrastruktur
2. Shopware-Standard (weniger Custom-Code)
3. Kunde hat bereits Erfahrung mit Automatisierung
4. Geringste Komplexität

**MVP-Rollout-Plan:**
```
Woche 1-2:  alp-shopware (MVP: Lesen + Rückfragen)
Woche 3-4:  alp-shopware (Phase 2: Code-Vorschläge)
Woche 5-6:  kraft-shopware (MVP)
Woche 7-8:  lupus (MVP)
Woche 9+:   Alle Kunden (Phase 3+)
```

### 2.4 Lesend vs. Schreibend

#### Entscheidungs-Matrix

| Betriebsmodus | Risiko | Wert | MVP | Phase 2 | Phase 3 | Phase 4 |
|---------------|--------|------|-----|---------|---------|---------|
| **Nur lesend** | ⭐ Niedrig | ⭐⭐ Medium | ✅ | ✅ | ✅ | ✅ |
| **Code-Vorschläge** | ⭐⭐ Medium | ⭐⭐⭐ Hoch | ❌ | ✅ | ✅ | ✅ |
| **PRs mit Review** | ⭐⭐⭐ Medium-Hoch | ⭐⭐⭐⭐ Sehr Hoch | ❌ | ❌ | ✅ | ✅ |
| **Autonom** | ⭐⭐⭐⭐⭐ Kritisch | ⭐⭐⭐⭐⭐ Maximal | ❌ | ❌ | ❌ | ✅ |

---

## 3. Phasen-Plan

### 3.1 Phase 1: Setup + Lesen + Rückfragen (Wochen 1-4)

#### Ziel
Agent kann Tickets lesen, Code analysieren und gezielte Rückfragen stellen. **Keine Code-Änderungen.**

#### Deliverables

| # | Deliverable | Owner | Deadline |
|---|-------------|-------|----------|
| 1.1 | Focalboard-Setup + API-Integration | Dev | Woche 1 |
| 1.2 | Bitbucket-Read-Only-Zugriff | Dev | Woche 1 |
| 1.3 | Kunden-Isolation implementiert | Dev | Woche 2 |
| 1.4 | Dev-Agent "Lesen + Analysieren" | Dev | Woche 3 |
| 1.5 | Rückfragen-Workflow (Slack/Email) | Dev | Woche 3 |
| 1.6 | Dokumentation der Analyseergebnisse | Dev | Woche 4 |
| 1.7 | Security-Review der Architektur | Security | Woche 4 |

#### Erfolgskriterien

- [ ] Agent liest Ticket korrekt aus
- [ ] Agent identifiziert relevante Code-Stellen
- [ ] Agent stellt sinnvolle Rückfragen bei Unklarheiten
- [ ] Kein Schreibzugriff auf Repositories
- [ ] Kosten < $50/Woche

---

### 3.2 Phase 2: Code-Vorschläge ohne Commit (Wochen 5-8)

#### Ziel
Agent erstellt Code-Vorschläge, die menschlich reviewed werden. **Keine automatischen Commits.**

#### Deliverables

| # | Deliverable | Owner | Deadline |
|---|-------------|-------|----------|
| 2.1 | Code-Generation-Engine | Dev | Woche 5 |
| 2.2 | Linting/Formatting-Integration | Dev | Woche 6 |
| 2.3 | Vorschlags-UI (Markdown-Diff) | Dev | Woche 6 |
| 2.4 | Review-Workflow mit Approval | Dev | Woche 7 |
| 2.5 | Tester-Agent (Basis-Version) | Dev | Woche 8 |
| 2.6 | Rollback-Prozess dokumentiert | DevOps | Woche 8 |

#### Erfolgskriterien

- [ ] Code-Vorschläge sind syntaktisch korrekt
- [ ] Vorschläge enthalten Erklärungen
- [ ] Menschliche Review-Pflicht vor Übernahme
- [ ] Ablehnung mit Feedback möglich
- [ ] Kosten < $100/Woche

---

### 3.3 Phase 3: Commits mit menschlichem Review (Wochen 9-14)

#### Ziel
Agent erstellt PRs mit automatisierten Checks. Menschlicher Review vor Merge.

#### Deliverables

| # | Deliverable | Owner | Deadline |
|---|-------------|-------|----------|
| 3.1 | PR-Automation (Create, Update) | Dev | Woche 9 |
| 3.2 | CI/CD-Integration für Agent-PRs | DevOps | Woche 10 |
| 3.3 | Automated Testing (Unit/Integration) | Dev | Woche 11 |
| 3.4 | Security-Scanning (Semgrep, Trivy) | Security | Woche 12 |
| 3.5 | Rollback-Automation | DevOps | Woche 13 |
| 3.6 | Monitoring & Alerting | DevOps | Woche 14 |

#### Erfolgskriterien

- [ ] PRs werden automatisch erstellt
- [ ] Alle Checks müssen grün sein
- [ ] Menschlicher Review vor Merge
- [ ] Rollbarkeit innerhalb 5 Minuten
- [ ] MTTR (Mean Time To Recovery) < 30 Minuten

---

### 3.4 Phase 4: Autonomer Betrieb (Wochen 15-20)

#### Ziel
Agent arbeitet weitgehend autonom bei Standard-Tickets. Mensch nur bei Exceptions.

#### Deliverables

| # | Deliverable | Owner | Deadline |
|---|-------------|-------|----------|
| 4.1 | Confidence-Scoring für Tickets | Dev | Woche 15 |
| 4.2 | Auto-Merge für Low-Risk-Changes | Dev | Woche 16 |
| 4.3 | Security-Agent vollständig | Security | Woche 17 |
| 4.4 | Advanced Monitoring (AIOps) | DevOps | Woche 18 |
| 4.5 | Self-Healing-Capabilities | Dev | Woche 19 |
| 4.6 | Odoo-Integration (statt Focalboard) | Dev | Woche 20 |

#### Erfolgskriterien

- [ ] 80% der Standard-Tickets autonom
- [ ] < 5% Rollback-Rate
- [ ] Security-Incidents = 0
- [ ] Kosten stabilisieren sich
- [ ] Kundenzufriedenheit ≥ 4.5/5

---

## 4. Rollback & Fehlerbehandlung

### 4.1 Rollback-Strategien

#### Rollback-Levels

| Level | Trigger | Methode | Zeit |
|-------|---------|---------|------|
| **L1: PR-Revert** | Code-Review-Feedback | Git Revert | Sofort |
| **L2: Branch-Reset** | Pre-Merge-Issue | Git Reset --hard | 2 Min |
| **L3: PR-Close** | Post-Merge-Problem | Git Revert + Close | 5 Min |
| **L4: Emergency** | Production-Issue | Hotfix-Branch | 15 Min |

#### Rollback-Workflow

```python
async def rollback_decision_matrix(error_context):
    """
    Automatische Entscheidungshilfe für Rollback
    """
    if error_context.severity == "critical":
        return await emergency_rollback(error_context)
    elif error_context.severity == "high":
        return await standard_rollback(error_context)
    elif error_context.severity == "medium":
        return await create_hotfix_ticket(error_context)
    else:
        return await log_and_monitor(error_context)
```

### 4.2 Fehlerhafter Commit - Rückgängig machen

#### Szenario: Falscher Code wurde committed

```bash
#!/bin/bash
# rollback-faulty-commit.sh

CUSTOMER_ID=$1
COMMIT_HASH=$2
REASON=$3

# 1. Revert erstellen
git revert --no-edit $COMMIT_HASH

# 2. Emergency-Label setzen
curl -X POST "$FOCALBOARD_API/cards/$TICKET_ID" \
  -d '{"labels": ["emergency-rollback"]}'

# 3. Notification senden
slack-notify "🚨 Rollback durchgeführt: $REASON"

# 4. Audit-Log
echo "$(date) | $CUSTOMER_ID | $COMMIT_HASH | $REASON" >> /var/log/agent-rollbacks.log
```

#### Automatische Rollback-Trigger

| Bedingung | Aktion | Benachrichtigung |
|-----------|--------|------------------|
| CI-Build failed | Block PR + Comment | Slack #agent-alerts |
| Security-Scan failed | Block PR + Alert | Slack #security |
| Tests failed | Block PR + Log | Email + Slack |
| Kunde beschwert sich | Emergency Rollback | Phone + Slack |
| Kosten > $20/Ticket | Pause + Review | Slack #cost-control |

### 4.3 Monitoring & Alerting

#### Monitoring-Stack

```
┌─────────────────────────────────────────────────────────────────┐
│  METRICS              │  LOGS              │  TRACES            │
│  ─────────            │  ────              │  ─────             │
│  Prometheus           │  Loki              │  Jaeger            │
│  + Grafana            │  + Grafana         │  + Grafana         │
├─────────────────────────────────────────────────────────────────┤
│  ALERTING: Prometheus Alertmanager → Slack / PagerDuty          │
└─────────────────────────────────────────────────────────────────┘
```

#### Key Metrics

| Metric | Warning | Critical | Alert-Kanal |
|--------|---------|----------|-------------|
| **LLM-Kosten/Stunde** | $20 | $50 | Slack #cost-control |
| **Failed Requests/Min** | 5 | 20 | Slack #agent-alerts |
| **Rollback-Rate** | 5% | 10% | Slack #quality |
| **Response Time** | 30s | 60s | Slack #performance |
| **Token Usage/Call** | 50k | 100k | Slack #efficiency |

#### Dashboard-Widgets

- [ ] **Kosten-Overview:** Tägliche/weekly Kosten pro Kunde
- [ ] **Ticket-Status:** Offen/In Progress/Done pro Agent
- [ ] **Success-Rate:** Erfolgreiche vs. fehlgeschlagene Tickets
- [ ] **Model-Usage:** Welche LLMs werden genutzt
- [ ] **Rollback-Historie:** Timeline der letzten 30 Tage

### 4.4 Menschliche Override-Möglichkeit

#### Override-Levels

| Level | Berechtigung | Methode | Audit-Trail |
|-------|--------------|---------|-------------|
| **Pause Agent** | Tech Lead | Slack-Command `/pause-agent` | ✅ |
| **Kill Switch** | Admin | Dashboard-Button | ✅ |
| **Token-Revoke** | Admin | Vault-UI | ✅ |
| **Deployment-Stop** | DevOps | CI/CD-Override | ✅ |

#### Emergency-Buttons

```yaml
# emergency-controls.yml
controls:
  - id: pause-all-agents
    label: "🛑 Alle Agenten pausieren"
    effect: Stop all task processing
    confirmation: true
    notify: ["admin", "on-call"]
    
  - id: revoke-openrouter
    label: "🔒 OpenRouter-Token sperren"
    effect: Block all LLM calls
    confirmation: true
    notify: ["admin", "finance"]
    
  - id: isolate-customer
    label: "🔒 Kunden isolieren"
    effect: Block all access for customer
    params: [customer_id]
    confirmation: true
    notify: ["admin", "customer-pm"]
```

---

## 5. Kosten-Schätzung

### 5.1 OpenRouter-Kosten pro Ticket-Typ

#### Token-Schätzung pro Aufgabe

| Ticket-Typ | Input Tokens | Output Tokens | Modell | Kosten |
|------------|--------------|---------------|--------|--------|
| **Bugfix (klein)** | 5k | 2k | Kimi 2.5 | $0.05 |
| **Bugfix (mittel)** | 15k | 5k | Claude 3.5 Sonnet | $0.35 |
| **Feature (klein)** | 10k | 8k | Kimi 2.5 | $0.20 |
| **Feature (mittel)** | 30k | 15k | Claude 3.5 Sonnet | $1.20 |
| **Feature (groß)** | 50k | 25k | GPT-4 | $3.50 |
| **Code-Review** | 20k | 3k | Claude 3.5 Sonnet | $0.45 |
| **Refactoring** | 25k | 20k | Claude 3.5 Sonnet | $1.80 |
| **Architektur-Analyse** | 40k | 10k | GPT-4 | $2.00 |
| **Rückfrage-Kontext** | 8k | 2k | Kimi 2.5 | $0.08 |

#### Monatliche Kosten-Schätzung (pro Kunde)

| Phase | Tickets/Monat | Ø Kosten/Ticket | Gesamt | Puffer (20%) | Budget |
|-------|---------------|-----------------|--------|--------------|--------|
| **MVP (Phase 1)** | 20 | $0.50 | $10 | $2 | **$12** |
| **Phase 2** | 30 | $2.00 | $60 | $12 | **$72** |
| **Phase 3** | 50 | $3.50 | $175 | $35 | **$210** |
| **Phase 4** | 80 | $3.00 | $240 | $48 | **$288** |

> **Hinweis:** Phase 4 ist günstiger pro Ticket durch Erfahrungsgewinn und effizientere Prompts.

#### Kosten-Prognose (3 Kunden)

| Phase | Kunde 1 | Kunde 2 | Kunde 3 | Gesamt |
|-------|---------|---------|---------|--------|
| **MVP** | $12 | - | - | $12 |
| **Phase 2** | $72 | $72 | - | $144 |
| **Phase 3** | $210 | $210 | $210 | $630 |
| **Phase 4** | $288 | $288 | $288 | $864 |

### 5.2 Infrastruktur-Kosten

#### Ressourcen-Bedarf

| Komponente | Specs | Kosten/Monat | Anbieter |
|------------|-------|--------------|----------|
| **App-Server** | 4 vCPU, 8GB RAM | $40 | Hetzner/DigitalOcean |
| **PostgreSQL** | 2 vCPU, 4GB RAM | $25 | Managed DB |
| **Redis** | 1 vCPU, 2GB RAM | $15 | Managed Cache |
| **ChromaDB** | 2 vCPU, 4GB RAM | $30 | Self-hosted |
| **Focalboard** | 1 vCPU, 2GB RAM | $10 | Self-hosted |
| **Monitoring** | Prometheus/Grafana | $20 | Self-hosted |
| **Backup-Speicher** | 100GB | $5 | S3-compatible |
| **Vault (Secrets)** | 1 vCPU, 2GB RAM | $15 | Self-hosted |

#### Gesamt-Infrastruktur (pro Umgebung)

| Umgebung | Ressourcen | Kosten/Monat |
|----------|------------|--------------|
| **Production** | Full Stack | $160 |
| **Staging** | 50% Scale | $80 |
| **Development** | Minimal | $40 |
| **Gesamt** | | **$280/Monat** |

### 5.3 Gesamtkosten-Übersicht

#### Monatliche Kosten nach Phase

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1 (MVP - 1 Kunde)                                       │
│  ─────────────────────────                                      │
│  OpenRouter:        $  12                                       │
│  Infrastruktur:     $ 160                                       │
│  ─────────────────────────                                      │
│  GESAMT:            $ 172                                       │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 2 (2 Kunden)                                            │
│  ────────────────────                                           │
│  OpenRouter:        $ 144                                       │
│  Infrastruktur:     $ 280                                       │
│  ─────────────────────────                                      │
│  GESAMT:            $ 424                                       │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 3 (3 Kunden)                                            │
│  ────────────────────                                           │
│  OpenRouter:        $ 630                                       │
│  Infrastruktur:     $ 280                                       │
│  ─────────────────────────                                      │
│  GESAMT:            $ 910                                       │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 4 (3 Kunden, autonom)                                   │
│  ─────────────────────────                                      │
│  OpenRouter:        $ 864                                       │
│  Infrastruktur:     $ 280                                       │
│  ─────────────────────────                                      │
│  GESAMT:            $1,144                                      │
└─────────────────────────────────────────────────────────────────┘
```

#### Jährliche Kosten-Projektion

| Jahr | Setup-Kosten | Laufend (Ø/Monat) | Gesamt |
|------|--------------|-------------------|--------|
| **Jahr 1** | $5,000 (Entwicklung) | $650 | $12,800 |
| **Jahr 2** | $1,000 (Wartung) | $850 | $11,200 |
| **Jahr 3** | $1,000 (Wartung) | $950 | $12,400 |

### 5.4 Cost-Control-Maßnahmen

#### Budget-Alerts

```yaml
# cost-alerts.yml
alerts:
  - threshold: 50%
    action: slack-notification
    channel: "#cost-control"
    
  - threshold: 80%
    action: email-notification
    recipients: ["admin", "finance"]
    
  - threshold: 100%
    action: hard-stop
    effect: Pause all non-critical agents
    requires_approval: true
```

#### Kosteneinsparungs-Strategien

| Strategie | Einsparung | Implementierung |
|-----------|------------|-----------------|
| **Caching** | 30-40% | Redis für häufige Queries |
| **Smart Model Switching** | 50-60% | Kimi für Simple, GPT nur für Complex |
| **Prompt Optimization** | 20-30% | Few-shot Prompts, Chunking |
| **Batching** | 10-20% | Mehrere Tasks zusammenfassen |
| **Context Pruning** | 15-25% | Irrelevante History entfernen |

---

## 6. Risiko-Matrix

### 6.1 Risiko-Übersicht

| Risiko | Eintrittswahrscheinlichkeit | Auswirkung | Gesamtrisiko | Mitigation |
|--------|---------------------------|------------|--------------|------------|
| **Cross-Customer-Contamination** | Niedrig | Kritisch | 🔴 Hoch | Multi-Layer-Isolation |
| **Fehlerhafter Code in Produktion** | Mittel | Kritisch | 🔴 Hoch | Review-Gate, Tests |
| **API-Token-Exposure** | Niedrig | Hoch | 🟡 Mittel | Vault, Rotation, Monitoring |
| **Kosten-Explosion** | Mittel | Mittel | 🟡 Mittel | Rate-Limiting, Alerts |
| **LLM-Downtime/Rate-Limit** | Mittel | Mittel | 🟡 Mittel | Fallback-Models |
| **Kunden-Unzufriedenheit** | Mittel | Hoch | 🟡 Mittel | MVP-Approach, Feedback |
| **Datenverlust** | Niedrig | Kritisch | 🔴 Hoch | Backups, Audit-Logs |
| **Compliance-Verstoß** | Niedrig | Kritisch | 🔴 Hoch | DSGVO-Design, Logging |

### 6.2 Risiko-Mitigation-Plan

#### Kritische Risiken (🔴)

| Risiko | Mitigation | Verantwortlich | Deadline |
|--------|------------|----------------|----------|
| Cross-Contamination | Container-Isolation + Validierung | DevOps | Woche 2 |
| Fehlerhafter Code | Review-Gate + Automated Tests | QA | Woche 4 |
| Datenverlust | 3-2-1 Backup-Strategie | DevOps | Woche 3 |
| Compliance | DSGVO-Impact-Assessment | Legal | Woche 4 |

---

## 7. Zusammenfassung & Nächste Schritte

### 7.1 Go/No-Go Checkliste

Vor Start des MVP müssen folgende Punkte erfüllt sein:

- [ ] **Sicherheit:**
  - [ ] Kunden-Isolation getestet und validiert
  - [ ] API-Token in Vault gespeichert
  - [ ] Rate-Limiting implementiert
  - [ ] Security-Review abgeschlossen

- [ ] **Infrastruktur:**
  - [ ] Focalboard läuft stabil
  - [ ] PostgreSQL + Redis eingerichtet
  - [ ] Monitoring (Grafana) konfiguriert
  - [ ] Backup-Strategie aktiv

- [ ] **Kunde:**
  - [ ] alp-shopware hat zugestimmt
  - [ ] Read-Only-Zugriff eingerichtet
  - [ ] Rückfragen-Kanal definiert
  - [ ] Escalation-Prozess geklärt

- [ ] **Team:**
  - [ ] Verantwortlicher Tech Lead benannt
  - [ ] On-Call-Rotation definiert
  - [ ] Dokumentation angelegt
  - [ ] Training durchgeführt

### 7.2 Zeitplan-Übersicht

```
Woche:  1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20
        │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
Phase 1:████████████████│   │   │   │   │   │   │   │   │   │   │   │   │   │   │
Phase 2:            │████████████████│   │   │   │   │   │   │   │   │   │   │
Phase 3:                            │████████████████████│   │   │   │   │   │
Phase 4:                                                │████████████████████│
```

### 7.3 Erfolgs-Definition

**Projekt ist erfolgreich, wenn:**

1. ✅ Keine Cross-Customer-Contamination
2. ✅ Rollback-Rate < 5% in Phase 3+
3. ✅ Kundenzufriedenheit ≥ 4.0/5
4. ✅ Kosten unter Budget
5. ✅ Security-Incidents = 0
6. ✅ 80% der Standard-Tickets autonom (Phase 4)

---

**Dokument-Version:** 1.0  
**Letzte Aktualisierung:** 20.02.2026  
**Autor:** AI-Assistant  
**Review-Status:** Pending
