# KI-Mitarbeiter System - Makefile

.PHONY: setup start stop restart logs clean status

# Initial setup
setup:
	@chmod +x setup.sh
	@./setup.sh

# Start all services
start:
	@docker-compose up -d
	@echo "✅ Services started. Frontend: http://localhost:3000 | API: http://localhost:8000"

# Stop all services
stop:
	@docker-compose down
	@echo "🛑 Services stopped"

# Restart services
restart: stop start

# View logs
logs:
	@docker-compose logs -f

# Clean up (removes containers and volumes)
clean:
	@docker-compose down -v
	@docker system prune -f
	@echo "🧹 Cleanup complete"

# Check status
status:
	@docker-compose ps

# Development: Install Python deps locally (not in Docker)
install:
	@pip install -r requirements.txt

# Development: Run agent worker locally
dev-agent:
	@python agent_worker.py

# Backup database
backup:
	@mkdir -p ~/ki-data/backups
	@cp ~/ki-data/kanban.db ~/ki-data/backups/kanban-$(shell date +%Y%m%d-%H%M%S).db
	@echo "💾 Database backed up"

# Show data directory size
disk-usage:
	@du -sh ~/ki-data/* 2>/dev/null || echo "No data yet"
	@echo "---"
	@du -sh .git 2>/dev/null || echo "No .git"
	@echo "---"
	@du -sh .
