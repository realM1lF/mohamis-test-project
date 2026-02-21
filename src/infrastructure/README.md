# DDEV Infrastructure for Mohami KI-Mitarbeiter

This module provides the infrastructure for managing multiple customer DDEV environments for Shopware development.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Agent Tools Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ DDEVExecute  │  │ DDEVTest     │  │ DDEVComposer │  │ DDEVStatus  │ │
│  │ DDEVGitSync  │  │ ShopwareCmd  │  │              │  │             │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────┘
          │                 │                 │                 │
          └─────────────────┴─────────────────┴─────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   Workspace Manager    │
                    │   (Customer Isolation) │
                    └───────────┬────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
    ┌─────▼─────┐         ┌─────▼─────┐         ┌─────▼─────┐
    │alp-shopware│         │kraft-shopware│         │   lupus   │
    │  DDEV Env  │         │  DDEV Env   │         │  DDEV Env │
    └────────────┘         └─────────────┘         └───────────┘
```

## Components

### 1. Workspace Manager (`workspace_manager.py`)

Central management of customer workspaces:

```python
from src.infrastructure.workspace_manager import get_workspace_manager

manager = get_workspace_manager()

# Setup a new workspace
success, message = manager.setup_workspace('alp-shopware')

# Start DDEV
success, message = manager.start_ddev('alp-shopware')

# Execute command
success, stdout, stderr = manager.execute_in_ddev('alp-shopware', 'bin/console cache:clear')

# Sync to Git
success, message = manager.sync_to_repo('alp-shopware', commit_message='Fix bug')
```

### 2. DDEV Manager (`ddev_manager.py`)

Advanced DDEV orchestration:

```python
from src.infrastructure.ddev_manager import DDEVManager

ddev = DDEVManager()

# List all projects
projects = ddev.list_all_projects()

# Create snapshot
ddev.snapshot_create('/path/to/project', name='before-migration')

# Health check
healthy, details = ddev.health_check('/path/to/project')
```

### 3. Agent Tools (`src/tools/ddev_tools.py`)

Tools for AI agent integration:

- `DDEVExecuteTool` - Execute arbitrary commands
- `DDEVShopwareCommandTool` - Run Shopware console commands
- `DDEVTestTool` - Run PHPUnit tests
- `DDEVComposerTool` - Manage Composer dependencies
- `DDEVStatusTool` - Check environment status
- `DDEVGitSyncTool` - Sync to Git repository

## Configuration

Customer configurations are defined in `config/customers.yaml`:

```yaml
customers:
  alp-shopware:
    display_name: "Alp-Shopware"
    ddev:
      project_name: "alp-shopware"
      php_version: "8.1"
      database:
        type: "mariadb"
        version: "10.4"
    shopware:
      version: "6.5.8.14"
    git:
      remote: "git@github.com:agency/alp-shopware.git"
      default_branch: "main"
    workspace:
      base_path: "~/ki-data/customer-workspaces/alp-shopware"
```

## CLI Usage

The setup script provides full CLI management:

```bash
# List all customers
python scripts/setup_customer_ddev.py --list

# Setup a customer
python scripts/setup_customer_ddev.py --customer alp-shopware --setup

# Start/stop DDEV
python scripts/setup_customer_ddev.py --customer alp-shopware --start
python scripts/setup_customer_ddev.py --customer alp-shopware --stop

# Run tests
python scripts/setup_customer_ddev.py --customer alp-shopware --test

# Execute command
python scripts/setup_customer_ddev.py --customer alp-shopware --exec "bin/console cache:clear"

# Sync to Git
python scripts/setup_customer_ddev.py --customer alp-shopware --sync --message "Fix bug"
```

## Makefile Targets

```bash
# Setup and management
make -f Makefile.ddev ddev-setup CUSTOMER=alp-shopware
make -f Makefile.ddev ddev-up CUSTOMER=alp-shopware
make -f Makefile.ddev ddev-down CUSTOMER=alp-shopware
make -f Makefile.ddev ddev-status CUSTOMER=alp-shopware

# Execute commands
make -f Makefile.ddev ddev-exec CUSTOMER=alp-shopware CMD="bin/console cache:clear"
make -f Makefile.ddev ddev-test CUSTOMER=alp-shopware
make -f Makefile.ddev ddev-sync CUSTOMER=alp-shopware

# Bulk operations
make -f Makefile.ddev ddev-all-up
make -f Makefile.ddev ddev-all-down

# Backups
make -f Makefile.ddev ddev-backup CUSTOMER=alp-shopware
make -f Makefile.ddev ddev-restore CUSTOMER=alp-shopware FILE=backup.sql.gz
```

## Docker Compose Integration

Start DDEV services alongside the main stack:

```bash
# Start with DDEV orchestrator
docker-compose -f docker-compose.yml -f docker-compose.ddev.yml --profile ddev up -d

# Start specific customer environment
docker-compose -f docker-compose.yml -f docker-compose.ddev.yml --profile alp-shopware up -d

# Start all customer environments
docker-compose -f docker-compose.yml -f docker-compose.ddev.yml \
  --profile alp-shopware --profile kraft-shopware --profile lupus up -d
```

## Network Isolation

Each customer has an isolated Docker network:

- `alp-network`: 172.28.10.0/24
- `kraft-network`: 172.28.20.0/24
- `lupus-network`: 172.28.30.0/24

## Shared Volumes

- `composer_cache`: Shared Composer cache across all environments
- `npm_cache`: Shared NPM cache
- `ddev_global`: Global DDEV configuration

## Security

- Customer workspaces are isolated by Docker networks
- Git operations use customer-specific credentials
- No cross-customer file system access
- DDEV containers run with limited privileges

## Troubleshooting

### DDEV not starting

```bash
# Check DDEV status
ddev status

# View logs
ddev logs

# Restart with cleanup
ddev restart
```

### Permission issues

```bash
# Fix file ownership
ddev exec sudo chown -R www-data:www-data /var/www/html

# Reset permissions
make -f Makefile.ddev ddev-exec CUSTOMER=alp-shopware CMD="sudo chmod -R 777 var"
```

### Database issues

```bash
# Reset database
ddev delete -y && ddev start

# Import from backup
ddev import-db --file=backup.sql.gz
```

## Testing

Run tests for the infrastructure:

```bash
# Run all tests
python -m pytest tests/infrastructure/

# Test specific component
python -m pytest tests/infrastructure/test_workspace_manager.py
```
