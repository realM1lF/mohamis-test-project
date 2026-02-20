#!/bin/bash
# Setup-Skript für KI-Mitarbeiter System
# Erstellt Daten-Verzeichnisse außerhalb des Git-Repos

echo "🔧 Setup KI-Mitarbeiter System..."

# Daten-Verzeichnis außerhalb des Repos
DATA_DIR="$HOME/ki-data"
mkdir -p "$DATA_DIR"/{chroma,redis,postgres,logs,customer-workspaces}

echo "✅ Daten-Verzeichnis erstellt: $DATA_DIR"

# Prüfe .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env nicht gefunden. Kopiere von .env.example..."
    cp .env.example .env 2>/dev/null || echo "Bitte .env manuell erstellen"
fi

# Erstelle leere DB falls nicht existiert
if [ ! -f "$DATA_DIR/kanban.db" ]; then
    echo "🗄️  Initialisiere Datenbank..."
    touch "$DATA_DIR/kanban.db"
fi

echo ""
echo "📁 Ordnerstruktur:"
echo "  Code (Git): $(pwd)"
echo "  Daten:      $DATA_DIR"
echo ""
echo "🚀 Starten mit: docker-compose up -d"
