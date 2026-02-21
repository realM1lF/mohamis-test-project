# Mohami KI-Mitarbeiter - Architektur V2

## Überblick

Die neue Architektur ermöglicht dynamisches Workspace-Management durch Repository-Cloning statt hardcoded DDEV-Konfigurationen.

## Kritischer Unterschied zur V1

| V1 (Alt) | V2 (Neu) |
|----------|----------|
| Hardcoded Kunden in docker-compose.ddev.yml | Dynamisches Cloning aus customers.yaml |
| DDEV als separate Container | DDEV läuft IM geklonten Repository |
| Manuelle Workspace-Erstellung | Automatisches setup_workspace() |
| Nur GitHub Support | GitHub + Bitbucket Support |
| Nur Shopware/PHP | Beliebige Tech-Stacks |

## Workflow

### 1. Konfiguration (durch Kunden)

```yaml
# config/customers.yaml
customers:
  test-customer:
    id: test-customer
    name: "Test Customer"
    git_provider: github
    repo_url: https://github.com/realM1lF/personal-ki-agents
    has_ddev: false
    default_branch: main
    workspace_path: ~/ki-data/workspaces/test-customer
    
    tech_stack:
      type: python
      version: "3.11"
```

### 2. Workspace Setup (durch Agent)

```python
from src.infrastructure.workspace_manager import get_workspace_manager

wm = get_workspace_manager()

# Cloned das Repo und startet DDEV wenn vorhanden
success, message = wm.setup_workspace("test-customer")
```

Was passiert:
1. Repository wird geklont nach `~/ki-data/workspaces/{customer}/`
2. Prüfung auf `.ddev/config.yaml`
3. Falls vorhanden: `ddev start` wird ausgeführt
4. Workspace ist bereit

### 3. Arbeit im Workspace

```python
# Befehl ausführen (in DDEV wenn verfügbar, sonst lokal)
success, stdout, stderr = wm.execute_command(
    customer_id="test-customer",
    command="python -m pytest",
    use_ddev=True  # Nutzt DDEV wenn verfügbar
)
```

### 4. Änderungen committen

```python
# Änderungen pullen
wm.pull_changes("test-customer")

# Änderungen commiten und pushen
wm.sync_to_repo(
    customer_id="test-customer",
    commit_message="Feature X implementiert"
)
```

## Komponenten

### RepositoryManager

Verwaltet alle Git-Operationen:
- `clone_repo()` - Klont Repository
- `pull_changes()` - Pullt Änderungen
- `push_changes()` - Committet und pusht
- `get_repo_info()` - Repository-Status

Unterstützt:
- GitHub (HTTPS + SSH)
- Bitbucket
- Private Repositories (mit Token)

### WorkspaceManager

Verwaltet die Workspaces:
- `setup_workspace()` - Richtet Workspace ein
- `execute_command()` - Führt Befehle aus
- `start_ddev()` / `stop_ddev()` - DDEV-Verwaltung
- `run_tests()` - Führt Tests aus
- `get_status()` - Workspace-Status

### DDEV Tools

Agent-Tools für die Integration:
- `workspace_setup` - Workspace initialisieren
- `ddev_execute` - Befehle ausführen
- `run_tests` - Tests laufen lassen
- `git_sync` - Änderungen pushen
- `git_pull` - Änderungen pullen
- `workspace_status` - Status prüfen
- `list_workspaces` - Alle Workspaces anzeigen

## Verzeichnisstruktur

```
~/ki-data/workspaces/
├── test-customer/              # Geklontes Repository
│   ├── .git/
│   ├── src/
│   ├── tests/
│   ├── .ddev/                  # Optional: DDEV Config
│   │   └── config.yaml
│   └── ...
├── shopware-customer/          # Anderer Kunde
│   ├── .ddev/                  # Mit DDEV
│   ├── html/                   # Shopware-Struktur
│   └── ...
└── ...
```

## Vorteile der neuen Architektur

1. **Flexibilität**: Beliebige Repositories, beliebige Tech-Stacks
2. **Einfachheit**: Keine hardcoded Container mehr
3. **Skalierbarkeit**: Neue Kunden = neue Eintrag in YAML
4. **Git-Nativ**: Vollständige Git-Integration
5. **Multi-Provider**: GitHub und Bitbucket Support

## Migration von V1

Alte docker-compose.ddev.yml wird gelöscht. Stattdessen:

1. `config/customers.yaml` mit neuem Format erstellen
2. Für jeden Kunden:
   - `repo_url` setzen
   - `has_ddev` auf true wenn DDEV-Config im Repo
   - `tech_stack` definieren
3. Agent ruft `setup_workspace()` statt docker-compose

## Beispiele

### Python Projekt ohne DDEV

```yaml
customers:
  my-python-app:
    id: my-python-app
    name: "My Python App"
    git_provider: github
    repo_url: https://github.com/user/my-app
    has_ddev: false
    default_branch: main
    tech_stack:
      type: python
      version: "3.11"
```

### Shopware Projekt mit DDEV

```yaml
customers:
  shopware-shop:
    id: shopware-shop
    name: "Shopware Shop"
    git_provider: github
    repo_url: https://github.com/user/shopware-shop
    has_ddev: true  # Repo enthält .ddev/config.yaml
    default_branch: main
    tech_stack:
      type: php
      version: "8.2"
      framework: shopware
```

### Private Bitbucket Repository

```yaml
customers:
  private-project:
    id: private-project
    name: "Private Project"
    git_provider: bitbucket
    repo_url: https://bitbucket.org/workspace/repo
    has_ddev: false
    auth_token: ${BITBUCKET_TOKEN}  # Umgebungsvariable
    tech_stack:
      type: node
      version: "18"
```

## Troubleshooting

### DDEV nicht gefunden
```bash
# DDEV installieren
curl -fsSL https://ddev.com/install.sh | bash
```

### Berechtigungsfehler beim Clone
- `auth_token` in customers.yaml setzen
- ODER: SSH-Key im Container hinterlegen

### Workspace existiert nicht
- `setup_workspace()` vor Arbeit ausführen
- Status mit `get_status()` prüfen
