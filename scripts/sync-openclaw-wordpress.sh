#!/usr/bin/env bash
# Verlinkt Skill + Plugin aus diesem Repo ins OpenClaw-Workspace (Symlinks).
# So gelten Aenderungen im Klon sofort am Zielort; erneut ausfuehren nach Pull.
#
# Nutzung:
#   ./scripts/sync-openclaw-wordpress.sh
#   OPENCLAW_WORKSPACE=/pfad/zum/workspace ./scripts/sync-openclaw-wordpress.sh
#   ./scripts/sync-openclaw-wordpress.sh --restart   # danach Gateway neu starten
#
set -euo pipefail

RESTART=false
for arg in "$@"; do
  case "$arg" in
    --restart|-r) RESTART=true ;;
    -h|--help)
      echo "Usage: $0 [--restart]"
      echo "  Symlinks openclaw-wordpress-skill -> ~/.openclaw/workspace/skills/wordpress-site-ops"
      echo "  Runs: npm install + openclaw plugins install -l (symlink) + enable"
      exit 0
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_SRC="$REPO_ROOT/openclaw-wordpress-skill"
PLUGIN_DIR="$REPO_ROOT/openclaw-wordpress-tools"
OPENCLAW_WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SKILL_DST="$OPENCLAW_WORKSPACE/skills/wordpress-site-ops"
OPENCLAW_BIN="${OPENCLAW_BIN:-openclaw}"

if [[ ! -d "$SKILL_SRC" ]]; then
  echo "Fehler: Skill-Ordner fehlt: $SKILL_SRC" >&2
  exit 1
fi
if [[ ! -d "$PLUGIN_DIR" ]]; then
  echo "Fehler: Plugin-Ordner fehlt: $PLUGIN_DIR" >&2
  exit 1
fi

if ! command -v "$OPENCLAW_BIN" &>/dev/null; then
  echo "Fehler: Befehl '$OPENCLAW_BIN' nicht gefunden (PATH pruefen oder OPENCLAW_BIN setzen)." >&2
  exit 1
fi

echo "==> OpenClaw-Workspace: $OPENCLAW_WORKSPACE"

mkdir -p "$OPENCLAW_WORKSPACE/skills"

if [[ -e "$SKILL_DST" ]] && [[ ! -L "$SKILL_DST" ]]; then
  echo "Fehler: $SKILL_DST existiert und ist kein Symlink." >&2
  echo "       Umbenennen oder loeschen, dann Skript erneut starten." >&2
  exit 1
fi

SKILL_SRC_ABS="$(cd "$SKILL_SRC" && pwd)"
ln -sfn "$SKILL_SRC_ABS" "$SKILL_DST"
echo "==> Skill-Symlink: $SKILL_DST -> $SKILL_SRC_ABS"

echo "==> Plugin: npm install"
(cd "$PLUGIN_DIR" && npm install --no-fund --no-audit)

echo "==> Plugin: openclaw plugins install -l (Symlink zum Repo)"
# -l = Development-Symlink laut Plugin-README
"$OPENCLAW_BIN" plugins install -l "$PLUGIN_DIR"

echo "==> Plugin: enable wordpress-site-tools"
"$OPENCLAW_BIN" plugins enable wordpress-site-tools || true

echo ""
echo "Fertig. Hinweise:"
echo "  - plugins.allow: [\"wordpress-site-tools\"] (OpenClaw-Warnung) und tools.allow (Agent-Tools), siehe references/CONNECTING.md."
echo "  - Nach Allowlist-/Plugin-Aenderungen: Gateway restart (nicht nur Chat /new); siehe Skill-README „Gateway vs. Chat“."
echo "  - WORDPRESS_* / Plugin-Config wie in openclaw-wordpress-skill/references/AUTH.md"
if [[ "$RESTART" == true ]]; then
  echo "  - Starte Gateway neu..."
  "$OPENCLAW_BIN" gateway restart || echo "WARN: gateway restart fehlgeschlagen (manuell ausfuehren)."
else
  echo "  - Bei Bedarf: $0 --restart  oder: $OPENCLAW_BIN gateway restart"
fi
