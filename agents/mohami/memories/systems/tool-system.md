# Tool-Use System

## Übersicht
Das Tool-System ermöglicht dem Agenten, Aktionen auf dem System durchzuführen. Tools sind als Python-Klassen implementiert und über eine zentrale Registry verfügbar.

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      TOOL ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌───────────┐  │
│   │  BaseTool    │◄────│  ToolRegistry│────►│  Tools    │  │
│   │  (Abstract)  │     │  (Central)   │     │  (Concrete)│  │
│   └──────────────┘     └──────────────┘     └─────┬─────┘  │
│          ▲                                        │        │
│          │         ┌──────────────┐              │        │
│          └─────────┤ FileReadTool │              │        │
│                    │ FileWriteTool│              │        │
│                    │ GitCommitTool│              │        │
│                    │ DDEVStartTool│              │        │
│                    └──────────────┘              │        │
│                                                  │        │
│                    ┌─────────────────────────────┘        │
│                    │                                      │
│                    ▼                                      │
│          ┌──────────────────┐                            │
│          │ ToolExecutor     │                            │
│          │ - Validierung    │                            │
│          │ - Ausführung     │                            │
│          │ - Fehlerhandling │                            │
│          └──────────────────┘                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tool-Kategorien

### 1. File Tools (`src/tools/file_tools.py`)
| Tool | Beschreibung |
|------|--------------|
| `file_read` | Liest Datei-Inhalt |
| `file_write` | Schreibt Datei |
| `file_delete` | Löscht Datei |
| `directory_list` | Listet Verzeichnis |
| `directory_create` | Erstellt Verzeichnis |

### 2. Git Tools (`src/tools/git_tools.py`)
| Tool | Beschreibung |
|------|--------------|
| `git_status` | Zeigt Git-Status |
| `git_diff` | Zeigt Unterschiede |
| `git_commit` | Erstellt Commit |
| `git_branch` | Verzweigung verwalten |
| `git_checkout` | Branch wechseln |

### 3. Code Tools (`src/tools/code_tools.py`)
| Tool | Beschreibung |
|------|--------------|
| `code_search` | Code durchsuchen |
| `code_replace` | Code ersetzen |
| `code_analyze` | Code analysieren |
| `test_run` | Tests ausführen |

### 4. DDEV Tools (`src/tools/ddev_tools.py`)
| Tool | Beschreibung |
|------|--------------|
| `ddev_start` | DDEV starten |
| `ddev_stop` | DDEV stoppen |
| `ddev_exec` | Befehl in DDEV ausführen |
| `ddev_import_db` | Datenbank importieren |

## Tool-Schema

Jedes Tool definiert ein JSON-Schema für Parameter:

```python
class FileReadTool(BaseTool):
    name = "file_read"
    description = "Reads a file from the filesystem"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        },
        "required": ["path"]
    }
```

## LLM-Integration

Tools können für LLM Function Calling formatiert werden:

```python
# OpenAI Format
schemas = registry.get_schemas_for_llm(format="openai")
# -> [{"type": "function", "function": {...}}]

# Anthropic Format
schemas = registry.get_schemas_for_llm(format="anthropic")
# -> [{"name": "...", "description": "...", "input_schema": {...}}]
```

## Tool-Ausführung

```python
from src.tools import ToolRegistry, ToolExecutor

# Registry initialisieren
registry = ToolRegistry()
registry.register(FileReadTool())
registry.register(FileWriteTool())

# Tool holen und ausführen
tool = registry.get("file_read")
result = await tool.execute({"path": "/tmp/test.txt"})

# Oder über Executor mit Validierung
executor = ToolExecutor(registry)
result = await executor.execute("file_read", {"path": "/tmp/test.txt"})
```

## Fehlerhandling

- **ValidationError**: Parameter nicht valide
- **ToolExecutionError**: Ausführung fehlgeschlagen
- **ToolNotFoundError**: Tool existiert nicht

## Best Practices

1. **Immer validieren**: Nutze ToolExecutor für automatische Validierung
2. **Idempotent**: Tools sollten idempotent sein (mehrfache Ausführung = gleiches Ergebnis)
3. **Logging**: Alle Tool-Aufrufe werden geloggt
4. **Sandbox**: File-Operations sind auf Arbeitsverzeichnis beschränkt
