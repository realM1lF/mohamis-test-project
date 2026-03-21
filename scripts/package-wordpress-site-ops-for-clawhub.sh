#!/usr/bin/env bash
# Baut einen Ordner wordpress-site-ops fuer ClawHub-Upload.
# ClawHub akzeptiert laut Pruefung nur Textdateien: .gitignore, .env.example und
# bundled/mu-plugin/*.php werden entfernt (PHP bleibt im vollstaendigen Git-Repo).
#
# Nutzung (aus Repo-Root):
#   ./scripts/package-wordpress-site-ops-for-clawhub.sh
# Ergebnis: build/clawhub-publish/wordpress-site-ops (im Projekt, Ordner build/ ist gitignored)
#
# Eigenes Zielverzeichnis (Elternordner – darin wird wordpress-site-ops angelegt):
#   ./scripts/package-wordpress-site-ops-for-clawhub.sh /pfad/zum/ausgabe-ordner
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SRC="$REPO_ROOT/openclaw-wordpress-skill"
PARENT="${1:-"$REPO_ROOT/build/clawhub-publish"}"
FINAL="$PARENT/wordpress-site-ops"

if [[ ! -d "$SRC" ]]; then
  echo "Fehler: Skill-Ordner fehlt: $SRC" >&2
  exit 1
fi

rm -rf "$PARENT"
mkdir -p "$PARENT"
cp -a "$SRC" "$FINAL"

rm -f "$FINAL/.gitignore" "$FINAL/.env.example"
rm -f "$FINAL/bundled/mu-plugin/openclaw-site-helper.php"

echo "==> ClawHub-Paket: $FINAL"
echo "    (ohne .gitignore, .env.example, openclaw-site-helper.php)"
echo ""
echo "Validierung:"
npx --yes skills-ref validate "$FINAL"
echo ""
echo "Naechster Schritt: bei ClawHub diesen Ordner waehlen:"
echo "  $FINAL"
