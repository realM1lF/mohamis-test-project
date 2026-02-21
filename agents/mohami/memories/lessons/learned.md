# Gelernte Lektionen

## Architektur-Entscheidungen

### ORPA-Workflow funktioniert gut
**Datum**: 2025-02-20
**Kontext**: Ticket-Verarbeitung

Der ORPA-Zyklus (Observe-Reason-Plan-Act) bietet eine klare Struktur:
- **Observe**: Kontext sammeln (Repository, Customer, History)
- **Reason**: Mit LLM analysieren
- **Plan**: Implementierung planen
- **Act**: Ausführen oder Rückfragen

**Ergebnis**: Bessere Entscheidungen, weniger Fehler.

---

### Memory-Systeme sind kritisch
**Datum**: 2025-02-20
**Kontext**: Multi-Agent Setup

Vier Gedächtnis-Schichten notwendig:
1. **Kurzzeit**: Aktive Verarbeitung
2. **Sitzung**: Chat-Verlauf (Redis, 24-48h)
3. **Langzeit**: Patterns & Wissen (ChromaDB)
4. **Episodisch**: Ticket-Historie (PostgreSQL)

**Ergebnis**: Kunden-Isolation funktioniert, Agent lernt dazu.

---

### Git Cache reduziert API-Calls drastisch
**Datum**: 2025-02-20
**Kontext**: GitHub Integration

Redis-basierter Git Cache für:
- Repository-Dateiliste
- File Contents
- Branches & Commits

Cache-TTL: 2-5 Minuten für verschiedene Datentypen.

**Ergebnis**: Weniger Rate-Limits, schnellere Verarbeitung.

---

## Technische Lektionen

### Tool-System: Registry Pattern
**Datum**: 2025-02-20

Zentrale Tool-Registry ermöglicht:
- Dynamische Tool-Entdeckung
- Kategorisierung (file, git, code, ddev)
- LLM-Schema-Generierung (OpenAI, Anthropic)

```python
registry = ToolRegistry()
registry.register(FileReadTool(), category="file")
schemas = registry.get_schemas_for_llm(format="openai")
```

---

### Agent Config Loading
**Datum**: 2025-02-20

Agenten-Konfiguration aus Markdown:
- `soul.md` → Persönlichkeit
- `rules.md` → Constraints
- `knowledge.md` → Fakten
- `memories/` → Systems, Links, Lessons

Ermöglicht schnelle Agenten-Erstellung ohne Code-Änderung.

---

### DDEV für Shopware-Projekte
**Datum**: 2025-02-20

DDEV funktioniert gut für:
- Lokale Shopware-Entwicklung
- Konsistente Umgebungen
- Einfache Datenbank-Importe

Integration als Tool: `ddev_start`, `ddev_exec`, etc.

---

## Best Practices

### Code-Generierung
1. **Immer .gitignore** mit anlegen
2. **README.md** mit sinnvollem Inhalt
3. **Commit-Messages** aussagekräftig
4. **Auf main nie direkt** pushen → PR erstellen

### Kommunikation
1. **Max 1 Rückfrage** pro Ticket
2. **Kurz und prägnant**: 2-3 Sätze max
3. **Deutsch** (außer Kunde wünscht anderes)
4. **Duzt Kunden** (außer explizit anders)

### Security
1. **NIE API-Keys** in Code
2. **NIE Kundendaten** teilen
3. **Environment-Variablen** für Secrets
4. **Kunden-Isolation** strikt einhalten

---

## Fehler & Lösungen

### Problem: Leere PRs
**Symptom**: PR wird erstellt aber ohne Änderungen
**Ursache**: Branch wurde erstellt aber keine Files committed
**Lösung**: File-Inhalt prüfen vor Commit, Fehler abfangen

### Problem: GitHub API Rate Limits
**Symptom**: 403 Forbidden
**Lösung**: Git Cache implementiert, TTL optimiert

### Problem: Memory-System nicht verfügbar
**Symptom**: Enhanced Agent startet nicht
**Lösung**: Graceful Degradation → Basic Agent

---

## Offene Fragen

1. **Multi-Agent Koordination**: Wie teilen sich Agents Tasks?
2. **Code-Review**: Automatisierte Reviews durch Agenten?
3. **Testing**: Automatisierte Tests für generierten Code?
4. **Deployment**: CD-Pipeline Integration?

---

## Meta-Lernen

### Was funktioniert gut
- ✅ Markdown-basierte Agent-Config
- ✅ Tool-Registry Pattern
- ✅ ORPA-Workflow
- ✅ Redis + ChromaDB Kombination
- ✅ Git Cache

### Was verbessert werden kann
- ⚠️ LLM-Kosten optimieren (Token-Usage)
- ⚠️ Fehler-Handling robuster machen
- ⚠️ Tests für Agent-Logik
- ⚠️ Monitoring & Observability
