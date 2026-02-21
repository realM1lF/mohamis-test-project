# DDEV - Lokale Entwicklungsumgebung

## Übersicht
DDEV ist eine Docker-basierte lokale Entwicklungsumgebung, die Shopware-Projekte containerisiert bereitstellt.

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      DDEV ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────────────────────────────────────────┐  │
│   │                Docker Container                      │  │
│   │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │  │
│   │  │   Web (PHP)  │  │   Database   │  │   Redis   │ │  │
│   │  │   Apache/Nginx│  │  MariaDB/MySQL│  │  Cache    │ │  │
│   │  └──────────────┘  └──────────────┘  └───────────┘ │  │
│   │         │                  │                       │  │
│   │         └──────────────────┴───────────────────────┘  │
│   │                         │                           │  │
│   │                  ┌──────┴──────┐                    │  │
│   │                  │  ddev-router │                    │  │
│   │                  │  (Reverse Proxy)                  │  │
│   │                  └─────────────┘                    │  │
│   └─────────────────────────────────────────────────────┘  │
│                         │                                    │
│                         ▼                                    │
│   ┌─────────────────────────────────────────────────────┐  │
│   │   Host-System (Dein Computer)                        │  │
│   │   - Projekt-Dateien (gemountet)                      │  │
│   │   - ddev CLI Tool                                   │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Grundbefehle

```bash
# Projekt starten
ddev start

# Projekt stoppen
ddev stop

# Vollständig entfernen (Container + Volumes)
ddev delete

# Projekt-Status
ddev status

# Logs anzeigen
ddev logs

# In Container einloggen
ddev ssh

# Befehl im Container ausführen
ddev exec <command>
ddev exec bin/console cache:clear
```

## Konfiguration

### `.ddev/config.yaml`
```yaml
name: alp-shopware
type: shopware6
docroot: public
php_version: "8.1"
webserver_type: apache-fpm
database:
  type: mariadb
  version: "10.4"

# Services
omit_containers: [dba]
webimage_extra_packages: [php8.1-redis]

# Hostname
additional_hostnames:
  - admin.alp-shopware.local
```

### `.ddev/docker-compose.redis.yaml`
```yaml
services:
  redis:
    container_name: ddev-${DDEV_SITENAME}-redis
    image: redis:7-alpine
    volumes:
      - redis:/data
    labels:
      com.ddev.site-name: ${DDEV_SITENAME}
      com.ddev.approot: $DDEV_APPROOT

volumes:
  redis:
```

## URLs

| Service | URL |
|---------|-----|
| Frontend | `https://<project>.ddev.site` |
| Admin | `https://<project>.ddev.site/admin` |
| Mailhog | `https://<project>.ddev.site:8026` |
| PHPMyAdmin | `https://<project>.ddev.site:8037` |

## Typische Workflows

### Shopware-Setup
```bash
# 1. DDEV starten
cd /projekte/alp-shopware
ddev start

# 2. Shopware installieren (falls neu)
ddev exec ./bin/console system:install --basic-setup

# 3. Cache leeren
ddev exec ./bin/console cache:clear

# 4. Assets bauen
ddev exec ./bin/console theme:compile
ddev exec ./bin/console assets:install
```

### Datenbank-Import
```bash
# SQL-Datei importieren
ddev import-db --src=database.sql.gz

# Oder über Adminer (https://<project>.ddev.site:8037)
```

### Plugin-Entwicklung
```bash
# Plugin aktivieren
ddev exec ./bin/console plugin:install MyPlugin
ddev exec ./bin/console plugin:activate MyPlugin

# Migrationen ausführen
ddev exec ./bin/console database:migrate --all MyPlugin
```

## DDEV im Agent-System

### DDEVManager (`src/infrastructure/ddev_manager.py`)
```python
from src.infrastructure import DDEVManager

ddev = DDEVManager(workspace_path="/projekte/alp-shopware")

# Starten
result = await ddev.start()

# Befehl ausführen
result = await ddev.exec("bin/console cache:clear")

# Status prüfen
status = await ddev.status()
```

### DDEV Tools (`src/tools/ddev_tools.py`)
```python
from src.tools import DDEVStartTool, DDEVExecTool

# Tool registrieren
registry.register(DDEVStartTool())
registry.register(DDEVExecTool())

# Ausführen
result = await ddev_start_tool.execute({
    "project_path": "/projekte/alp-shopware"
})

result = await ddev_exec_tool.execute({
    "project_path": "/projekte/alp-shopware",
    "command": "bin/console theme:compile"
})
```

## Troubleshooting

```bash
# Container-Probleme
ddev poweroff  # Alle DDEV-Container stoppen
ddev start     # Neu starten

# Port-Konflikte
ddev config --router-http-port=8080 --router-https-port=8443

# Logs anzeigen
ddev logs -f

# Alles zurücksetzen
ddev delete -Oy
ddev start
```

## Integration mit Agent-Workflow

1. **Repository geklont** → DDEV prüfen/starten
2. **Änderungen gemacht** → Cache leeren
3. **Tests ausführen** → DDEV exec vendor/bin/phpunit
4. **Datenbank-Änderungen** → Migrationen ausführen
