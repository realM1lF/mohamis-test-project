# 🧹 Projekt-Aufräumungs-Report

**Datum:** 23. Februar 2026  
**Analyst:** Kimi + Team  
**Scope:** Root-Level Dateien & Verzeichnisstruktur

---

## 📊 Zusammenfassung

| Kategorie | Dateien gesamt | DELETE | MOVE | KEEP | MERGE |
|-----------|----------------|--------|------|------|-------|
| **Test-Dateien** | 8 | 3 | 1 | 0 | 4 |
| **Dokumentation** | 10 | 2 | 5 | 3 | 2 |
| **Demo/Debug** | 6 | 1 | 3 | 2 | 0 |
| **Konfiguration** | 9 | 0 | 3 | 5 | 1 |
| **GESAMT** | **33** | **6** | **12** | **10** | **7** |

**Potenzielle Reduzierung:** ~40% weniger Dateien im Root-Verzeichnis

---

## 🔴 DELETE (Löschen)

Diese Dateien können sofort gelöscht werden:

### Test-Dateien (3)
| Datei | Grund |
|-------|-------|
| `test_import.py` | Veraltet, hardcoded `/app` Pfad, redundant |
| `test_architecture_v2_simple.py` | Veraltet, testet nicht-existierende Datei |
| `test_architecture_v2.py` | Veraltet, redundant zu `tests/infrastructure/` |

### Dokumentation (2)
| Datei | Grund |
|-------|-------|
| `ARCHITECTURE_V2_SUMMARY.md` | Redundant zu `docs/ARCHITECTURE_V2.md` |
| `PHASE_3_PLAN.md` | Veraltet, Inhalt in ROADMAP.md integrieren |

### Demo/Debug (1)
| Datei | Grund |
|-------|-------|
| `agent_worker_debug.py` | Veraltet, `agent_worker.py` hat bessere Debug-Funktionen |

**⚠️ Wichtig:** Inhalt von `PHASE_3_PLAN.md` und `QA_ANALYSIS.md` vorher in ROADMAP.md übernehmen!

---

## 🟡 MOVE (Verschieben)

### Nach `tests/` (1)
| Datei | Ziel |
|-------|------|
| `test_intelligent_agent_migration.py` | `tests/integration/test_agent_migration.py` |

### Nach `scripts/` (3)
| Datei | Ziel |
|-------|------|
| `demo_agent.py` | `scripts/demo_agent.py` |
| `demo_tool_agent.py` | `scripts/demo_tools.py` (umbenennen) |
| `load_memories.py` | `scripts/load_memories.py` |

### Nach `docker/` (2) - NEU ERSTELLEN
| Datei | Ziel |
|-------|------|
| `Dockerfile.backend` | `docker/Dockerfile.backend` |
| `Dockerfile.worker` | `docker/Dockerfile.worker` |

### Nach `docs/` (5)
| Datei | Ziel |
|-------|------|
| `ANALYSIS.md` | `docs/analysis/incident-2026-02-22-pr-quality-gate.md` |
| `DDEV_INTEGRATION.md` | `docs/guides/ddev-integration.md` |
| `FEATURES.md` | `docs/internal/memory-tuning-discussion.md` |
| `03-Bitbucket-Integration.md` | `docs/integrations/bitbucket/` (aufsplitten) |
| `QA_ANALYSIS.md` | Inhalt in ROADMAP.md integrieren, dann löschen |

### Sonstige (1)
| Datei | Ziel |
|-------|------|
| `pytest.ini` | `config/pytest.ini` (optional) |

---

## 🟢 KEEP (Behalten im Root)

Diese Dateien müssen im Root-Verzeichnis bleiben:

### Kern-Projektdateien
| Datei | Begründung |
|-------|------------|
| `README.md` | Standard-Projekt-Übersicht |
| `ROADMAP.md` | Master-Roadmap (aktuell halten!) |
| `IDEAS.md` | Vision-Dokument (lebendig) |
| `requirements.txt` | Standard-Location für Python-Deps |

### Produktiv-Code
| Datei | Begründung |
|-------|------------|
| `agent_worker.py` | Haupt-Worker-Prozess |

### Build & Deployment
| Datei | Begründung |
|-------|------------|
| `docker-compose.yml` | Docker Compose erwartet diese Datei im Root |
| `Makefile` | Standard-Location für Makefiles |

### Sicherheit & Konfiguration
| Datei | Begründung |
|-------|------------|
| `.env` | Enthält Secrets (ist bereits in .gitignore) |
| `.gitignore` | Muss im Repository-Root liegen |

**⚠️ WICHTIG:** `.env` enthält sensible Tokens! Diese sollten rotiert werden.

---

## 🔵 MERGE (Zusammenführen)

### Test-Dateien zusammenführen
| Quelle | Ziel |
|--------|------|
| `test_import_detailed.py` + `verify_imports.py` | `tests/unit/test_imports.py` (neu) |
| `test_github_connection.py` | `tests/integration/test_git_providers.py` (neu) |
| `test_integration.py` | `tests/integration/test_system.py` (neu) |

### Dokumentation zusammenführen
| Quelle | Ziel |
|--------|------|
| `PHASE_3_PLAN.md` | Inhalt in `ROADMAP.md` integrieren |
| `QA_ANALYSIS.md` | Inhalt in `ROADMAP.md` integrieren |

### Makefiles zusammenführen
| Quelle | Ziel |
|--------|------|
| `Makefile.ddev` | In `Makefile` integrieren oder als `.ddev.mk` inkludieren |

---

## 📁 Empfohlene neue Verzeichnisstruktur

```
/home/rin/Work/personal-ki-agents/
│
├── 📄 ROOT-LEVEL (10 Dateien)
│   ├── README.md
│   ├── ROADMAP.md
│   ├── IDEAS.md
│   ├── requirements.txt
│   ├── agent_worker.py
│   ├── docker-compose.yml
│   ├── Makefile
│   ├── .env (⚠️ Secrets!)
│   ├── .env.example (NEU!)
│   └── .gitignore
│
├── 📁 agents/ (bereits vorhanden)
│   └── mohami/
│       ├── soul.md
│       ├── rules.md
│       ├── knowledge.md
│       └── memories/
│
├── 📁 config/
│   ├── customers.yaml
│   └── pytest.ini (optional)
│
├── 📁 customers/ (bereits verschoben)
│   └── test-customer/
│
├── 📁 docker/ (NEU)
│   ├── Dockerfile.backend
│   └── Dockerfile.worker
│
├── 📁 docs/
│   ├── ARCHITECTURE_V2.md
│   ├── doc_sources_cron.md
│   │
│   ├── 📁 analysis/ (NEU)
│   │   └── incident-2026-02-22-pr-quality-gate.md
│   │
│   ├── 📁 guides/ (NEU)
│   │   └── ddev-integration.md
│   │
│   ├── 📁 internal/ (NEU)
│   │   └── memory-tuning-discussion.md
│   │
│   └── 📁 integrations/ (NEU)
│       └── bitbucket/
│           ├── index.md
│           ├── authentication.md
│           ├── repository-management.md
│           ├── security.md
│           └── ddev-workflow.md
│
├── 📁 scripts/ (erweitert)
│   ├── create_agent.py
│   ├── setup_customer_ddev.py
│   ├── fetch_doc_sources.py
│   ├── demo_agent.py (verschoben)
│   ├── demo_tools.py (verschoben + umbenannt)
│   └── load_memories.py (verschoben)
│
├── 📁 src/ (bereits vorhanden)
│
├── 📁 tests/ (erweitert)
│   ├── integration/
│   │   ├── test_agent_migration.py (verschoben)
│   │   ├── test_git_providers.py (neu)
│   │   └── test_system.py (neu)
│   └── unit/
│       └── test_imports.py (neu)
│
└── 📁 [andere Ordner: data, frontend, logs, pm]
```

---

## ⚠️ Kritische Hinweise

### 1. Sicherheitsproblem: `.env`
Die `.env` Datei enthält **sensible Tokens**:
- GitHub Token
- Kimi API Key  
- OpenRouter API Key

**Empfohlene Aktionen:**
1. Sofort: Tokens rotieren (neu generieren)
2. `.env.example` erstellen mit Dummy-Werten
3. Dokumentation: Wie man `.env` aus `.env.example` erstellt

### 2. Docker Compose Anpassungen
Wenn Dockerfiles verschoben werden:
```yaml
# docker-compose.yml Zeile 16
build:
  context: .
  dockerfile: docker/Dockerfile.backend  # ← NEUER PFAD
```

### 3. Makefile.ddev Merge
Option A: In Haupt-Makefile integrieren  
Option B: Als `.ddev.mk` inkludieren:
```makefile
# Am Ende von Makefile
-include .ddev.mk
```

---

## 🎯 Ausführungsreihenfolge

### Phase 1: Vorbereitung (Sicherheit)
1. `.env` Tokens rotieren
2. `.env.example` erstellen
3. `.env` in `.gitignore` prüfen (bereits vorhanden)

### Phase 2: Löschen (Schnelle Gewinne)
1. `test_import.py` löschen
2. `test_architecture_v2_simple.py` löschen
3. `test_architecture_v2.py` löschen
4. `ARCHITECTURE_V2_SUMMARY.md` löschen
5. `agent_worker_debug.py` löschen

### Phase 3: Verschieben (Struktur)
1. `mkdir -p docker docs/analysis docs/guides docs/internal docs/integrations/bitbucket`
2. Dockerfiles verschieben
3. Dokumentation verschieben
4. Scripts verschieben
5. Tests verschieben

### Phase 4: Mergen (Inhalt)
1. PHASE_3_PLAN.md → ROADMAP.md
2. QA_ANALYSIS.md → ROADMAP.md
3. Test-Dateien zusammenführen
4. Makefiles zusammenführen

### Phase 5: Anpassen (Konfiguration)
1. `docker-compose.yml` Pfade anpassen
2. `Makefile` aktualisieren
3. `README.md` aktualisieren

---

## 📈 Erwartetes Ergebnis

| Metrik | Vorher | Nachher | Reduktion |
|--------|--------|---------|-----------|
| Dateien im Root | 33 | 10 | -70% |
| Verzeichnisse im Root | 16 | 16 | - |
| Test-Dateien (Root) | 8 | 0 | -100% |
| Docker-Dateien (Root) | 2 | 0 | -100% |
| Dokumentation (Root) | 10 | 3 | -70% |

**Resultat:** Ein sauberes, professionelles Projekt-Layout!

---

## 🤔 Nächste Schritte

1. **Diesen Report genehmigen**
2. **Token-Rotation durchführen** (Sicherheit)
3. **Phase 1-2 ausführen** (Löschen - schnelle Gewinne)
4. **Phase 3-5 schrittweise** umsetzen
5. **README.md aktualisieren** mit neuer Struktur

Soll ich mit der Umsetzung beginnen oder möchtest du Anpassungen am Plan?
