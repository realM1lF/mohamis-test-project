# Standalone-Repository (nur dieses Plugin)

Canonical: **https://github.com/realM1lF/openclaw-wordpress-tool**

Wenn du **nur** dieses Repo geklont hast (ohne Monorepo `personal-ki-agents`), gelten die **relativen** Verweise im [README](README.md) auf `../openclaw-wordpress-skill/` nicht.

## Skill-Dokumentation (`wordpress-site-ops`)

Der Skill heisst auf ClawHub typisch **`wordpress-site-ops`**. Nach Installation im OpenClaw-Workspace liegen die Referenzen z. B. unter:

`skills/wordpress-site-ops/references/`

Dort findest du u. a.:

| Thema | Datei im Skill-Workspace |
|-------|---------------------------|
| Anbindung, Topologien, Verifikation | `CONNECTING.md` |
| Auth / Env / Secrets | `AUTH.md` |
| DDEV | `DDEV.md` |
| WP-CLI-Presets | `WPCLI_PRESETS.md` |

Offizielle Links: [OpenClaw Skills](https://docs.openclaw.ai/tools/skills), [Agent Tools](https://docs.openclaw.ai/plugins/agent-tools), [Building Plugins](https://docs.openclaw.ai/plugins/building-plugins).

## Optional: MU-Helfer auf der WordPress-Seite

PHP-Helfer liegt im **Skill-Repo** unter `bundled/mu-plugin/` (nicht in diesem Plugin-Repo). Nach Skill-Install: Datei aus dem Workspace-Ordner `skills/wordpress-site-ops/bundled/mu-plugin/` nach `wp-content/mu-plugins/` kopieren (siehe Skill-`MU_HELPER.md`).

## Maintainer: Export aus dem Monorepo

Wer im uebergeordneten Repo **personal-ki-agents** entwickelt und hier nur veroeffentlicht: dort liegt das Skript `scripts/export-openclaw-wordpress-tools-for-github.sh` sowie `docs/openclaw-wordpress/CLAWHUB_PUBLISH.md` (im Standalone-Klon dieser Pfade gibt es nicht).
