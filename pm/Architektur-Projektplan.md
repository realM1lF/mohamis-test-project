# Projektplan: Multi-Agent KI-Mitarbeiter-System für Shopware-Agentur

## 1. Gesamtarchitektur

### 1.1 Architektur-Übersicht (High-Level)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  CLI Tool   │  │  VS Code    │  │  Web Dashboard│  │  Ticket-System      │ │
│  │  (kimi-cli) │  │  Extension  │  │  (optional) │  │  Integration        │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────┼────────────────────┼────────────┘
          │                │                │                    │
          └────────────────┴────────────────┴────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Master Orchestrator Agent                         │    │
│  │  - Eingabeanalyse & Intent-Klassifizierung                          │    │
│  │  - Agent-Selektion & Routing                                        │    │
│  │  - Kunden-Kontext-Resolution                                        │    │
│  │  - Workflow-Koordination                                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────┼─────────────────────────────────────┐   │
│  │                                 ▼                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ Developer   │  │   Tester    │  │  Security   │  │  Context    │  │   │
│  │  │   Agent     │  │   Agent     │  │   Agent     │  │  Manager    │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │   │
│  │         │                │                │                │         │   │
│  │         └────────────────┴────────────────┴────────────────┘         │   │
│  │                              │                                       │   │
│  │                              ▼                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │                    Agent Communication Bus                      │ │   │
│  │  │         (Message Queue für Agent-zu-Agent-Kommunikation)        │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER ISOLATION LAYER                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      Customer Context Manager                            ││
│  │  ┌──────────────┬──────────────┬──────────────┬──────────────────────┐  ││
│  │  │ alp-shopware │kraft-shopware│    lupus     │    [neuer Kunde]     │  ││
│  │  │  SW 6.5.8.14 │  SW 6.7.6.2  │  SW 6.7.2.2  │                      │  ││
│  │  │   PHP 8.1    │   PHP 8.2    │   PHP 8.2    │                      │  ││
│  │  │   DDEV Env   │   DDEV Env   │   DDEV Env   │                      │  ││
│  │  └──────────────┴──────────────┴──────────────┴──────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEMORY & STATE LAYER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Short-Term  │  │   Session    │  │   Long-Term  │  │   Episodic       │ │
│  │  (In-Memory) │  │   (Redis)    │  │  (ChromaDB)  │  │  (PostgreSQL)    │ │
│  │              │  │              │  │              │  │                  │ │
│  │ - Aktueller  │  │ - Chat-Verl. │  │ - Code-Embed.│  │ - Entscheidungs- │ │
│  │   Kontext    │  │ - Sitzungs-  │  │ - Doku-Embed.│  │   geschichte     │ │
│  │ - Temp. Vars │  │   state      │  │ - Pattern    │  │ - Lessons        │ │
│  │              │  │ - Customer   │  │ - Erfahrungen│  │   Learned        │ │
│  │              │  │   Isolation  │  │              │  │ - Agent-Events   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLM PROVIDER LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         OpenRouter.ai                                │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│  │  │   GPT-5     │  │   Claude    │  │  Kimi 2.5   │  │   Gemini    │ │    │
│  │  │  (OpenAI)   │  │  (Anthropic)│  │ (Moonshot)  │  │  (Google)   │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │    │
│  │                                                                     │    │
│  │  Routing-Strategie:                                                 │    │
│  │  - Komplexe Logik → Claude                                          │    │
│  │  - Code-Generierung → Kimi 2.5                                      │    │
│  │  - Schnelle Antworten → GPT-5                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TOOL & EXECUTION LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    DDEV     │  │   Git CLI   │  │  Shopware   │  │   Code-Analyse      │ │
│  │   Wrapper   │  │   Tools     │  │    CLI      │  │   Tools             │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   PHPStan   │  │   Psalm     │  │  PHPUnit    │  │   Security Scanner  │ │
│  │   /Rector   │  │             │  │             │  │   (Snyk/Dependabot) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Kunden-Isolations-Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Customer Isolation Manager                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────┐    ┌─────────────────────────────────────┐ │
│  │  Customer Registry  │    │       Isolated Execution Contexts    │ │
│  │                     │    │                                      │ │
│  │ alp-shopware        │───▶│  ┌───────────────────────────────┐  │ │
│  │ ├── repo: alp/sw6   │    │  │ alp-shopware Context          │  │ │
│  │ ├── sw_version: 6.5 │    │  │ ├── Working Directory:        │  │ │
│  │ ├── php_version: 8.1│    │  │ │   /workspace/alp-shopware   │  │ │
│  │ ├── ddev_project: alp│   │  │ ├── DDEV Container: alp-ddev  │  │ │
│  │ └── plugins: [...]  │    │  │ ├── Git Remote: origin/alp    │  │ │
│  │                     │    │  │ ├── Plugin Registry           │  │ │
│  │ kraft-shopware      │───▶│  │ └── Env: ISOLATED_CUSTOMER=alp│  │ │
│  │ ├── repo: kraft/sw6 │    │  └───────────────────────────────┘  │ │
│  │ ├── sw_version: 6.7 │    │                                      │ │
│  │ ├── php_version: 8.2│    │  ┌───────────────────────────────┐  │ │
│  │ └── ...             │───▶│  │ kraft-shopware Context        │  │ │
│  │                     │    │  │ ├── Working Directory:        │  │ │
│  │ lupus               │    │  │ │   /workspace/kraft-shopware │  │ │
│  │ └── ...             │───▶│  │ ├── DDEV Container: kraft-ddev│  │ │
│  │                     │    │  │ └── Env: ISOLATED_CUSTOMER=...│  │ │
│  │ [neuer Kunde]       │    │  └───────────────────────────────┘  │ │
│  │ └── ...             │───▶│  ┌───────────────────────────────┐  │ │
│  │                     │    │  │ lupus Context                 │  │ │
│  └─────────────────────┘    │  │ └── ...                       │  │ │
│                             │  └───────────────────────────────┘  │ │
│                             └─────────────────────────────────────┘ │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Isolation Enforcement (auf Agent-Ebene)                         ││
│  │  • Jeder Agent erhält CustomerContext bei Instanziierung        ││
│  │  • Alle File-System-Ops über CustomerFileSystem-Adapter         ││
│  │  • Alle Git-Ops über CustomerGit-Adapter mit validiertem Remote ││
│  │  • Alle DDEV-Kommandos über CustomerDDEV-Adapter                ││
│  │  • Cross-Customer-Zugriff wird blockiert                        ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Agenten-Rollen und Verantwortlichkeiten

### 2.1 Übersicht der Agenten-Typen

| Agent | Primäre Rolle | Verantwortlichkeiten | Shopware-Kompetenz |
|-------|--------------|---------------------|-------------------|
| **Master Orchestrator** | Koordination & Routing | Intent-Analyse, Agent-Selektion, Workflow-Management, Konflikt-Lösung | Alle Versionen (Meta) |
| **Developer Agent** | Code-Generierung & Modifikation | Plugin-Entwicklung, Bugfixes, Feature-Implementierung, Code-Reviews | SW 6.5/6.6/6.7, PHP 8.1/8.2 |
| **Tester Agent** | Qualitätssicherung | Test-Generierung, Test-Ausführung, Coverage-Analyse, Regression-Tests | PHPUnit, Cypress, Jest |
| **Security Agent** | Sicherheitsanalyse | Dependency-Scanning, Code-Audit, CVE-Checks, Compliance | Snyk, Composer-Audit |
| **Context Manager** | Gedächtnis & Kontext | Memory-Verwaltung, Knowledge-Retrieval, Kontext-Zusammenführung | - |

### 2.2 Detaillierte Agenten-Spezifikationen

#### 2.2.1 Master Orchestrator Agent

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Master Orchestrator Agent                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INPUT PROCESSING                                                    │
│  ├── Natural Language Understanding (NLU)                           │
│  │   └── Intent-Klassifizierung:                                     │
│  │       • CODE_GENERATION    → Developer Agent                      │
│  │       • BUG_FIX            → Developer Agent (+ Tester)           │
│  │       • SECURITY_AUDIT     → Security Agent                       │
│  │       • TEST_CREATION      → Tester Agent                         │
│  │       • MULTI_STEP_TASK    → Workflow Orchestration               │
│  │                                                                  │
│  ├── Customer Context Resolution                                     │
│  │   └── Keywords/Aliases Mapping:                                   │
│  │       • "alp", "alp-shopware" → alp-shopware Context             │
│  │       • "kraft" → kraft-shopware Context                          │
│  │       • "lupus" → lupus Context                                   │
│  │                                                                  │
│  └── Priority & Urgency Assessment                                   │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  WORKFLOW ORCHESTRATION                                              │
│  ├── Single-Agent Tasks                                              │
│  │   └── Direkte Delegation an spezialisierten Agenten               │
│  │                                                                  │
│  ├── Multi-Agent Workflows                                           │
│  │   └── Sequential/Parallel Execution Patterns:                     │
│  │       • Dev → Test → Security Pipeline                           │
│  │       • Parallel Analysis (Security + Code Quality)               │
│  │       • Iterative Feedback Loops                                  │
│  │                                                                  │
│  └── Human-in-the-Loop Decision Points                               │
│      └── Bei: Deployment, Breaking Changes, Security Issues          │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  OUTPUT SYNTHESIS                                                    │
│  ├── Ergebnis-Aggregation von mehreren Agenten                       │
│  ├── Konflikt-Erkennung und -Lösung                                  │
│  └── Klare, strukturierte Antwort an User                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Kernkompetenzen:**
- Fehlerfreie Intent-Erkennung auch bei vagen Anfragen
- Optimierte Agent-Selektion basierend auf Kontext und Verfügbarkeit
- Effiziente Workload-Verteilung
- Fehlerbehandlung und Recovery-Strategien

#### 2.2.2 Developer Agent

| Aspekt | Details |
|--------|---------|
| **Primäre Aufgaben** | Plugin-Entwicklung, Feature-Implementierung, Bugfixing, Code-Reviews |
| **Code-Generierung** | PHP 8.1/8.2, JavaScript/Vue.js, TWIG-Templates, XML-Konfigurationen |
| **Shopware-Spezifisch** | Plugin-Struktur, Service-Container, Events/Subscriber, API-Integration |
| **Tools** | DDEV-Integration, Git-Operations, Composer, PHPStan, Rector |

**Spezialisierungen pro Shopware-Version:**

```yaml
alp-shopware (SW 6.5.8.14, PHP 8.1):
  - Legacy-Plugin-Struktur (src/ statt nachfolgende Strukturen)
  - Ältere Event-System-Nutzung
  - PHP 8.1 Features (keine 8.2 Features)
  - Besondere Beachtung bei SW 6.5 → 6.6 Migration-Pfaden

kraft-shopware (SW 6.7.6.2, PHP 8.2):
  - Aktuellste Plugin-Struktur
  - PHP 8.2 Features (Readonly-Klassen, null/false/true als Typen)
  - Moderne Shopware APIs

lupus (SW 6.7.2.2, PHP 8.2):
  - Ähnlich kraft-shopware, aber spezifische Anpassungen möglich
  - Version-spezifische Edge-Case-Kenntnis
```

**Developer Agent - ORPA Workflow:**

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ OBSERVE  │───▶│  REASON  │───▶│   PLAN   │───▶│   ACT    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
• Task-Beschreibung • Anforderungs-  • Code-Struktur  • Code-
• Bestehender Code  •   analyse      •   Planung      • Generierung
• Shopware-Version  • Pattern-       • File-          • Git-Commit
• Kunden-Plugins    •   Matching     •   Änderungen   • DDEV-Test
• Fehlermeldungen   • Constraint-    • Abhängigkeiten • Code-Review
                    •   Identifikation
```

#### 2.2.3 Tester Agent

| Aspekt | Details |
|--------|---------|
| **Primäre Aufgaben** | Test-Generierung, Test-Ausführung, Coverage-Analyse, Regression-Testing |
| **Test-Typen** | Unit-Tests (PHPUnit), Integrationstests, E2E-Tests (Cypress/Playwright) |
| **Shopware-Spezifisch** | Service-Test-Setup, Database-Fixtures, Storefront-Tests |
| **Tools** | PHPUnit, Cypress, Codeception, Jest, Coverage-Tools |

**Test-Strategien pro Kunde:**

| Kunde | Test-Setup | Besonderheiten |
|-------|-----------|----------------|
| alp-shopware | PHPUnit 9.x, eigene Test-DB | Legacy-Test-Strukturen |
| kraft-shopware | PHPUnit 10.x, DDEV-Integration | Moderne Test-Features |
| lupus | PHPUnit 10.x | Kundenspezifische Test-Config |

#### 2.2.4 Security Agent

| Aspekt | Details |
|--------|---------|
| **Primäre Aufgaben** | Dependency-Scanning, Code-Audit, CVE-Monitoring, Compliance-Checks |
| **Scan-Bereiche** | Composer-Dependencies, npm-Pakete, Custom-Code, Konfigurationen |
| **Shopware-Spezifisch** | Plugin-Security, API-Endpoint-Sicherheit, Permission-Checks |
| **Tools** | Snyk, GitHub Dependabot, Composer-Audit, PHP Security Checker |

**Security-Check-Pipeline:**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Dependency Scan │───▶│  Code Analysis  │───▶│  Compliance     │
│                 │    │                 │    │  Check          │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
• composer audit  │    • PHPStan Security│    • Shopware CS    │
• npm audit       │    • Psalm Taint     │    • OWASP Top 10   │
• Snyk scan       │    • Custom Rules    │    • GDPR Patterns  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                ▼
                    ┌─────────────────────┐
                    │   Risk Assessment   │
                    │   & Prioritization  │
                    └─────────────────────┘
```

#### 2.2.5 Context Manager Agent

| Aspekt | Details |
|--------|---------|
| **Primäre Aufgaben** | Memory-Verwaltung, Knowledge-Retrieval, Kontext-Zusammenführung, Episodisches Lernen |
| **Memory-Typen** | Kurzzeit (In-Memory), Sitzung (Redis), Langzeit (ChromaDB), Episodisch (PostgreSQL) |
| **Retrieval-Methoden** | Semantic Search, Keyword Search, Hybrid Retrieval |
| **Spezialfunktionen** | Cross-Customer Pattern-Erkennung, Lessons Learned, Code-Similarity |

---

## 3. ORPA-Workflow-Implementierung

### 3.1 ORPA als Fundamentales Muster

Das ORPA-Muster (Observe-Reason-Plan-Act) bildet die Grundlage für alle Agenten-Operationen:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORPA STATE MACHINE                                   │
│                                                                              │
│     ┌─────────┐         ┌─────────┐         ┌─────────┐         ┌─────────┐ │
│     │  IDLE   │────────▶│OBSERVING│────────▶│REASONING│────────▶│PLANNING │ │
│     └─────────┘  Input  └─────────┘  Parse  └─────────┘Analyze └─────────┘ │
│         ▲                                              │            │       │
│         │                                              │            │       │
│         │         ┌────────────────────────────────────┘            │       │
│         │         │                                                 ▼       │
│         │         │                                            ┌─────────┐  │
│         │         │                                            │ ACTING  │  │
│         │         │                                            └─────────┘  │
│         │         │                                                 │       │
│         │         └─────────────────────────────────────────────────┘       │
│         │                              Output / Feedback                      │
│         │                                                                     │
│     ┌─────────┐                                                             │
│     │  ERROR  │◀────────────────────────────────────────────────────────────┤
│     └─────────┘  Exception / Failure                                        │
│         │                                                                   │
│         └───────────────────────────────────────────────────────────────────┤
│                              Recovery / Retry                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 ORPA pro Agent-Typ

#### Developer Agent - ORPA-Implementierung

```python
class DeveloperAgentORPA:
    
    def observe(self, task_input: TaskInput) -> Observation:
        """
        Sammelt alle relevanten Informationen für die Aufgabe
        """
        return Observation(
            # Task-spezifisch
            task_description=task_input.description,
            requirements=extract_requirements(task_input),
            
            # Kunden-Kontext
            customer_context=self.customer_manager.get_context(
                task_input.customer_id
            ),
            
            # Code-Kontext
            existing_code=self.file_system.read_relevant_files(
                task_input.file_paths,
                customer_id=task_input.customer_id
            ),
            
            # Projekt-Kontext
            related_plugins=self.plugin_registry.get_for_customer(
                task_input.customer_id
            ),
            
            # Historischer Kontext
            similar_tasks=self.memory.retrieve_similar(
                task_input.description,
                task_type="development",
                limit=5
            ),
            
            # Shopware-spezifisch
            shopware_version=self.get_shopware_version(
                task_input.customer_id
            ),
            php_version=self.get_php_version(
                task_input.customer_id
            )
        )
    
    def reason(self, observation: Observation) -> Reasoning:
        """
        Analysiert die Beobachtungen und bestimmt die beste Herangehensweise
        """
        # LLM-basierte Reasoning-Phase
        reasoning_prompt = self.build_reasoning_prompt(observation)
        
        return Reasoning(
            # Verständnis der Aufgabe
            task_understanding=llm.analyze(reasoning_prompt),
            
            # Identifikation von Patterns
            applicable_patterns=self.pattern_matcher.find_matches(
                observation.task_description,
                observation.shopware_version
            ),
            
            # Constraint-Erkennung
            constraints=self.constraint_analyzer.analyze(
                observation.customer_context,
                observation.existing_code
            ),
            
            # Risiko-Einschätzung
            risk_assessment=self.assess_risks(observation),
            
            # Vorauswahl von Lösungsansätzen
            solution_approaches=llm.generate_approaches(reasoning_prompt)
        )
    
    def plan(self, reasoning: Reasoning) -> Plan:
        """
        Erstellt einen detaillierten Ausführungsplan
        """
        return Plan(
            # Schritt-für-Schritt Plan
            steps=self.plan_generator.generate(reasoning),
            
            # File-Operationen
            file_operations=self.plan_file_changes(reasoning),
            
            # Abhängigkeiten zwischen Schritten
            dependencies=self.map_dependencies(reasoning),
            
            # Rollback-Strategie
            rollback_plan=self.create_rollback_plan(reasoning),
            
            # Validations-Checkpoints
            validation_points=self.define_validations(reasoning),
            
            # Human-in-the-Loop Entscheidungspunkte
            decision_points=self.identify_decision_points(reasoning)
        )
    
    def act(self, plan: Plan) -> ActionResult:
        """
        Führt den Plan aus und überwacht die Ergebnisse
        """
        results = []
        
        for step in plan.steps:
            # Pre-Validation
            if not self.validate_preconditions(step):
                raise PreconditionError(step)
            
            # Ausführung
            result = self.execute_step(step)
            results.append(result)
            
            # Post-Validation
            if not self.validate_result(step, result):
                # Rollback bei Fehler
                self.execute_rollback(plan.rollback_plan, results)
                raise ExecutionError(step, result)
            
            # Memory-Update
            self.memory.store_step_result(step, result)
            
            # Checkpoint für Human-in-the-Loop
            if step.id in plan.decision_points:
                return ActionResult(
                    status="AWAITING_DECISION",
                    completed_steps=results,
                    pending_decision=step
                )
        
        return ActionResult(
            status="COMPLETED",
            results=results,
            summary=self.generate_summary(results)
        )
```

### 3.3 ORPA für Multi-Agent-Koordination

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Multi-Agent ORPA Orchestration                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SCENARIO: Feature-Implementierung mit Security-Review                       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PHASE 1: MASTER OBSERVE                                              │  │
│  │  ├── Eingabe: "Implementiere B2B-Preisregeln für Kraft-Shopware"     │  │
│  │  ├── Kunden-Resolution: kraft-shopware                                │  │
│  │  ├── Intent: CODE_GENERATION + SECURITY_SENSITIVE                     │  │
│  │  └── Workflow-Typ: SEQUENTIAL_WITH_SECURITY_GATE                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PHASE 2: DEVELOPER AGENT ORPA                                        │  │
│  │                                                                       │  │
│  │  OBSERVE:  ├── Kraft-Shopware Context (SW 6.7.6.2, PHP 8.2)          │  │
│  │            ├── Bestehende B2B-Plugins analysieren                     │  │
│  │            ├── Preisregel-System verstehen                            │  │
│  │            └── Ähnliche Implementierungen aus Memory                  │  │
│  │                                                                       │  │
│  │  REASON:   ├── Pattern: B2B-Suite Integration                         │  │
│  │            ├── Constraint: Kompatibilität mit B2B Sellers Plugin      │  │
│  │            └── Approach: Custom Rule Builder Extension                │  │
│  │                                                                       │  │
│  │  PLAN:     ├── 1. Entity erstellen                                    │  │
│  │            ├── 2. Service implementieren                              │  │
│  │            ├── 3. Admin-UI erweitern                                  │  │
│  │            └── 4. Tests schreiben                                     │  │
│  │                                                                       │  │
│  │  ACT:      └── [Code-Generierung]                                     │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PHASE 3: SECURITY AGENT ORPA (GATE)                                  │  │
│  │                                                                       │  │
│  │  OBSERVE:  ├── Neuer Code vom Developer Agent                         │  │
│  │            ├── B2B-Preisregel-Implementierung                         │  │
│  │            └── Sensitive Operation: Preisberechnung                   │  │
│  │                                                                       │  │
│  │  REASON:   ├── Risiko: SQL-Injection in Filter-Logik möglich          │  │
│  │            ├── Risiko: Price-Manipulation durch Input                 │  │
│  │            └── Focus: Input Validation & Authorization                │  │
│  │                                                                       │  │
│  │  PLAN:     ├── 1. Static Analysis (PHPStan Security)                  │  │
│  │            ├── 2. Taint Analysis (Psalm)                              │  │
│  │            ├── 3. Manual Code Review Patterns                         │  │
│  │            └── 4. Authorization Flow Check                            │  │
│  │                                                                       │  │
│  │  ACT:      └── [Security-Scan durchführen]                            │  │
│  │                                                                       │  │
│  │  RESULT:   ├── CRITICAL: SQL-Injection gefunden                       │  │
│  │            │   → RÜCKGABE an Developer Agent                          │  │
│  │            └── oder PASSED → Weiter zu Tester                         │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│              ┌─────────────────────┴─────────────────────┐                   │
│              │ Issue Found                               │ No Issues         │
│              ▼                                           ▼                   │
│  ┌───────────────────────┐                  ┌───────────────────────────┐    │
│  │ RETURN TO DEVELOPER   │                  │ TESTER AGENT ORPA         │    │
│  │ (mit Security Report) │                  │ [Test-Generierung &       │    │
│  └───────────────────────┘                  │  Ausführung]              │    │
│                                             └───────────────────────────┘    │
│                                                                           ▼  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  PHASE 4: MASTER SYNTHESIZE                                           │  │
│  │  ├── Ergebnisse aller Agenten aggregieren                             │  │
│  │  ├── Finalen Report generieren                                        │  │
│  │  ├── Empfohlene nächste Schritte                                      │  │
│  │  └── Memory: Episodic Learning speichern                              │  │
│  │     └── "B2B-Preisregeln in SW 6.7: Sicherheitsfallen"               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. LLM-Orchestrierungs-Strategie

### 4.1 Provider-Routing über OpenRouter

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LLM Routing & Selection Engine                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  REQUEST ANALYSIS                                                            │
│  ├── Task-Typ: code_generation | analysis | reasoning | chat               │
│  ├── Komplexität: simple | moderate | complex                              │
│  ├── Kontext-Größe: kurz | mittel | lang                                   │
│  └── Latenz-Anforderung: realtime | interactive | background               │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ROUTING DECISION MATRIX                                                     │
│                                                                              │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐  │
│  │    GPT-5        │    Claude 3.5   │   Kimi 2.5      │    Gemini 2.0   │  │
│  │    (OpenAI)     │   (Anthropic)   │  (Moonshot)     │    (Google)     │  │
│  ├─────────────────┼─────────────────┼─────────────────┼─────────────────┤  │
│  │ • Schnell       │ • Komplexe      │ • Code-Gen      │ • Langer        │  │
│  │ • Zuverlässig   │   Reasoning     │ • Kontext       │   Kontext       │  │
│  │ • Allzweck      │ • Sicherheits-  │ • Multilingual  │ • Multimodal    │  │
│  │ • Gut für Chat  │   Analyse       │ • Gut für SW    │ • Backup        │  │
│  │                 │ • Große Context │                 │                 │  │
│  ├─────────────────┼─────────────────┼─────────────────┼─────────────────┤  │
│  │ Latenz: ★★★★★  │ Latenz: ★★★☆☆  │ Latenz: ★★★★☆  │ Latenz: ★★★★☆  │  │
│  │ Code:   ★★★★☆  │ Code:   ★★★★☆  │ Code:   ★★★★★  │ Code:   ★★★☆☆  │  │
│  │ Context:★★★☆☆  │ Context:★★★★★  │ Context:★★★★★  │ Context:★★★★★  │  │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘  │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ROUTING RULES (Default)                                                     │
│                                                                              │
│  ┌─────────────────────────────┬──────────────────────────────────────────┐ │
│  │ Aufgabe                     │ Empfohlener Provider                     │ │
│  ├─────────────────────────────┼──────────────────────────────────────────┤ │
│  │ Plugin-Code generieren      │ Kimi 2.5 (bester PHP/SW Code)            │ │
│  │ Komplexes Debugging         │ Claude 3.5 (Reasoning)                   │ │
│  │ Schnelle Chat-Antwort       │ GPT-5 (niedrige Latenz)                  │ │
│  │ Security-Analyse            │ Claude 3.5 (sorgfältig, Context)         │ │
│  │ Große Codebase analysieren  │ Kimi 2.5 (200k Context)                  │ │
│  │ Multi-File Refactoring      │ Kimi 2.5 (Code-Verständnis)              │ │
│  │ Dokumentation schreiben     │ Claude 3.5 (Qualität)                    │ │
│  └─────────────────────────────┴──────────────────────────────────────────┘ │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FALLBACK STRATEGY                                                           │
│  ├── Primary: Konfigurierter Provider für Task-Typ                          │
│  ├── Fallback 1: Alternativer Provider (bei Timeout)                        │
│  ├── Fallback 2: Lighter Model (bei Rate Limit)                             │
│  └── Fallback 3: Lokal gehostetes Model (bei Ausfall)                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Model-Konfiguration pro Agent

| Agent | Primär-Modell | Fallback | Konfiguration |
|-------|--------------|----------|---------------|
| Master Orchestrator | GPT-5 | Claude 3.5 | temp=0.3, max_tokens=2048 |
| Developer Agent | Kimi 2.5 | Claude 3.5 | temp=0.2, max_tokens=4096 |
| Tester Agent | Kimi 2.5 | GPT-5 | temp=0.1, max_tokens=2048 |
| Security Agent | Claude 3.5 | Kimi 2.5 | temp=0.1, max_tokens=4096 |
| Context Manager | Kimi 2.5 | GPT-5 | temp=0.0, max_tokens=1024 |

### 4.3 Prompt-Templating & Versioning

```yaml
# prompt_registry.yaml
version: "1.0.0"

prompts:
  developer_code_generation:
    template: "prompts/developer/code_gen_v2.txt"
    variables:
      - shopware_version
      - php_version
      - customer_context
      - existing_code
      - requirements
    provider_overrides:
      kimi-2.5:
        system_prompt: "You are an expert Shopware 6 developer..."
        
  security_audit:
    template: "prompts/security/audit_v1.txt"
    variables:
      - code_to_analyze
      - dependency_tree
      - customer_security_profile
    provider_overrides:
      claude-3.5:
        system_prompt: "You are a security-focused code reviewer..."

  orchestrator_intent:
    template: "prompts/orchestrator/intent_v1.txt"
    provider_overrides:
      gpt-5:
        max_tokens: 512
```

---

## 5. Technologie-Stack Empfehlung

### 5.1 Core Framework & Libraries

| Kategorie | Technologie | Version | Begründung |
|-----------|-------------|---------|------------|
| **Framework** | LangGraph | ^0.2.x | State-Machine-basierte Agent-Orchestrierung |
| **LLM-Integration** | LangChain | ^0.3.x | Standardisierte LLM-Interfaces |
| **Provider-Proxy** | OpenRouter SDK | latest | Unified API für Multiple Provider |
| **Memory** | ChromaDB | ^0.5.x | Vektor-Datenbank für Long-Term Memory |
| **Session-Store** | Redis | 7.x | Schneller Session-State & Caching |
| **Episodic-DB** | PostgreSQL | 16.x | Strukturierte Speicherung von Erfahrungen |

### 5.2 Shopware-Integration

| Komponente | Technologie | Nutzung |
|------------|-------------|---------|
| **Lokale Entwicklung** | DDEV | Container-Isolation pro Kunde |
| **Code-Analyse** | PHPStan | Static Analysis |
| **Refactoring** | Rector | Automated Code Transformations |
| **Testing** | PHPUnit | Unit & Integration Tests |
| **E2E-Testing** | Cypress | Storefront-Tests |
| **Code-Quality** | PHP-CS-Fixer | Coding Standards |

### 5.3 Kunden-Spezifische DDEV-Konfiguration

```yaml
# customer_contexts.yaml
customers:
  alp-shopware:
    display_name: "Alp-Shopware"
    ddev:
      project_name: "alp-shopware"
      project_type: "shopware6"
      php_version: "8.1"
      webserver_type: "nginx-fpm"
      database:
        type: "mysql"
        version: "8.0"
    shopware:
      version: "6.5.8.14"
      composer_packages:
        - "shopware/core:6.5.8.14"
        - "shopware/storefront:6.5.8.14"
        - "shopware/administration:6.5.8.14"
    custom_plugins:
      - name: "netgrade/AlpCore"
        path: "custom/plugins/AlpCore"
      - name: "netgrade/AlpCheckout"
        path: "custom/plugins/AlpCheckout"
    external_plugins:
      - "store.shopware.com/b2bsellerssuite"
    git:
      remote: "git@github.com:agency/alp-shopware.git"
      default_branch: "main"
    
  kraft-shopware:
    display_name: "Kraft-Shopware"
    ddev:
      project_name: "kraft-shopware"
      php_version: "8.2"
    shopware:
      version: "6.7.6.2"
    custom_plugins:
      - name: "netgrade/KraftB2B"
        path: "custom/plugins/KraftB2B"
    git:
      remote: "git@github.com:agency/kraft-shopware.git"
      default_branch: "develop"
      
  lupus:
    display_name: "Lupus"
    ddev:
      project_name: "lupus-shopware"
      php_version: "8.2"
    shopware:
      version: "6.7.2.2"
    git:
      remote: "git@github.com:agency/lupus.git"
      default_branch: "main"
```

### 5.4 Projekt-Struktur

```
src/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py              # Abstrakte Base-Klasse mit ORPA
│   ├── master_orchestrator.py     # Zentraler Koordinator
│   ├── developer_agent.py         # Code-Generierung & Modifikation
│   ├── tester_agent.py            # Test-Automatisierung
│   ├── security_agent.py          # Security-Scanning
│   └── context_manager.py         # Gedächtnis-Management
│
├── core/
│   ├── __init__.py
│   ├── orpa.py                    # ORPA-State-Machine Implementierung
│   ├── config.py                  # Konfigurations-Management
│   ├── exceptions.py              # Custom Exceptions
│   └── logging.py                 # Structured Logging
│
├── customer/
│   ├── __init__.py
│   ├── context_manager.py         # Customer Isolation Manager
│   ├── filesystem_adapter.py      # Isolierter File-System-Zugriff
│   ├── git_adapter.py             # Isolierter Git-Zugriff
│   ├── ddev_adapter.py            # DDEV-Integration
│   └── registry.py                # Customer Registry & Discovery
│
├── memory/
│   ├── __init__.py
│   ├── base.py                    # Memory-Interface
│   ├── short_term.py              # In-Memory Buffer
│   ├── session.py                 # Redis-basiert
│   ├── long_term.py               # ChromaDB-basiert
│   ├── episodic.py                # PostgreSQL-basiert
│   └── embeddings.py              # Embedding-Generierung
│
├── llm/
│   ├── __init__.py
│   ├── router.py                  # LLM-Routing-Logik
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── openrouter.py          # OpenRouter-Integration
│   │   ├── fallback.py            # Fallback-Strategien
│   │   └── caching.py             # Response-Caching
│   └── prompts/
│       ├── __init__.py
│       ├── registry.py            # Prompt-Verwaltung
│       ├── developer/
│       ├── security/
│       ├── tester/
│       └── orchestrator/
│
├── tools/
│   ├── __init__.py
│   ├── base.py                    # Tool-Interface
│   ├── shopware/
│   │   ├── plugin_generator.py
│   │   ├── migration_helper.py
│   │   └── api_client.py
│   ├── ddev/
│   │   ├── container_manager.py
│   │   └── command_executor.py
│   ├── git/
│   │   ├── repository.py
│   │   └── operations.py
│   └── analysis/
│       ├── phpstan.py
│       ├── rector.py
│       └── security_scanner.py
│
├── interfaces/
│   ├── __init__.py
│   ├── cli.py                     # CLI-Interface
│   ├── vscode_extension/          # VS Code Extension (separat)
│   └── api.py                     # REST API (optional)
│
├── config/
│   ├── agents.yaml                # Agent-Konfiguration
│   ├── customers.yaml             # Kunden-Konfiguration
│   ├── llm.yaml                   # LLM-Routing-Konfiguration
│   └── prompts/                   # Prompt-Templates
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/
│   ├── setup.py                   # Initialisierung
│   └── migrate.py                 # Datenbank-Migrationen
│
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### 5.5 Infrastruktur-Stack

| Komponente | Empfehlung | Begründung |
|------------|------------|------------|
| **Runtime** | Python 3.12+ | Moderne Python-Features, Performance |
| **Container** | Docker + Docker Compose | Entwicklungs-Isolation |
| **Task Queue** | Celery + Redis | Hintergrund-Jobs, Agent-Kommunikation |
| **API-Server** | FastAPI (optional) | Wenn Web-Interface benötigt |
| **Monitoring** | Prometheus + Grafana | Metriken & Alerting |
| **Logging** | ELK Stack oder Loki | Zentrales Log-Management |

---

## 6. Implementierungs-Roadmap (Architektur-Fokus)

| Phase | Fokus | Deliverables | Dauer |
|-------|-------|--------------|-------|
| **Phase 1** | Foundation | Core-ORPA, Customer-Isolation, Memory-Layer | 2 Wochen |
| **Phase 2** | Developer Agent | Plugin-Generierung, DDEV-Integration, Git-Workflow | 2 Wochen |
| **Phase 3** | Multi-Agent | Tester + Security Agent, Agent-Kommunikation | 2 Wochen |
| **Phase 4** | Orchestration | Master Orchestrator, komplexe Workflows | 1 Woche |
| **Phase 5** | Polish | CLI, VS Code Extension, Monitoring | 1 Woche |

---

## 7. Risiken & Mitigationen

| Risiko | Impact | Mitigation |
|--------|--------|------------|
| LLM-Halluzinationen bei Code-Gen | Hoch | Multi-Layer-Validation, PHPStan-Integration |
| Kunden-Isolation verletzt | Kritisch | Strict Adapters, Automated Tests |
| Context-Window-Überschreitung | Mittel | Intelligent Chunking, Memory-Hierarchie |
| DDEV-Performance | Mittel | Container-Optimierung, Caching |
| API-Kosten (OpenRouter) | Mittel | Caching, Model-Tier-Routing |

---

*Dieser Architektur-Plan bildet die Grundlage für die Entwicklung des Multi-Agent KI-Mitarbeiter-Systems.*
