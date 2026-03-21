#!/usr/bin/env bash
# Exportiert openclaw-wordpress-tools fuer ein **eigenes** GitHub-Repo (ohne node_modules).
# Empfohlen vor dem ersten Push, statt `git init` direkt im Monorepo-Unterordner.
#
# Nutzung (aus Repo-Root):
#   ./scripts/export-openclaw-wordpress-tools-for-github.sh
# Ergebnis: build/openclaw-wordpress-tools-github/ (im Projekt, Ordner build/ ist gitignored)
#
# Eigenes Zielverzeichnis:
#   ./scripts/export-openclaw-wordpress-tools-for-github.sh /pfad/zum/export
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC="$REPO_ROOT/openclaw-wordpress-tools"
DEST="${1:-"$REPO_ROOT/build/openclaw-wordpress-tools-github"}"

if [[ ! -d "$SRC" ]]; then
  echo "Fehler: Plugin-Ordner fehlt: $SRC" >&2
  exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST"
rsync -a \
  --exclude 'node_modules/' \
  --exclude '.git/' \
  --exclude 'dist/' \
  "$SRC/" "$DEST/"

echo "==> Plugin-Export: $DEST"
echo "    (ohne node_modules, ohne .git, ohne dist/)"
echo ""
echo "Naechste Schritte:"
echo "  1. Auf GitHub: leeres Repository anlegen (z. B. openclaw-wordpress-tools)."
echo "  2. cd $(printf '%q' "$DEST")"
echo "  3. git init && git add . && git commit -m \"Initial: OpenClaw plugin wordpress-site-tools\""
echo "  4. git remote add origin git@github.com:realM1lF/openclaw-wordpress-tool.git"
echo "     (oder HTTPS: https://github.com/realM1lF/openclaw-wordpress-tool.git)"
echo "  5. git branch -M main && git push -u origin main"
echo ""
echo "Canonical Plugin-URL in Doku: docs/openclaw-wordpress/CLAWHUB_PUBLISH.md"
