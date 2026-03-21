# OpenClaw nativ vs. Plugin `wordpress-site-tools`

Der Skill **`wordpress-site-ops`** soll **kein** paralleles OpenClaw bauen. Stattdessen: WordPress-spezifische, policy-bewusste Schritte ueber das Plugin; alles andere ueber **eingebaute** OpenClaw-Werkzeuge (Namen je nach Gateway-Version, siehe [OpenClaw Tools](https://docs.openclaw.ai/tools)).

## Kurzuebersicht

| Aufgabe | Bevorzugt | Fallback |
|---------|-----------|----------|
| WP-Daten lesen/schreiben (REST) | **`wordpress_rest_request`** | Shell **`exec`** + `curl` (mit Quotes/Escaping, [SAFETY.md](SAFETY.md)) |
| WP-CLI mit Allowlist/Profil | **`wordpress_wp_cli`** + `wpCliProfile` oder `wpCliAllowPrefixes` | **`exec`** + `wp` ([SAFETY.md](SAFETY.md), [WPCLI_PRESETS.md](WPCLI_PRESETS.md)) |
| Erstkontakt / Anbindung pruefen | **`wordpress_connection_check`** | Manuell [CONNECTING.md](CONNECTING.md) |
| Medien-Datei hochladen (multipart) | **`wordpress_media_upload`** (wenn freigegeben) | `curl` mit `-F` / Browser |
| Dateien unter `wp-content/plugins/<slug>/` (list/read/write, begrenzt) | **`wordpress_plugin_files`** (wenn freigegeben, `WORDPRESS_PATH` gesetzt) | Workspace-Dateizugriff / `exec` |
| **Inside-WP-Diagnose** (Extensions, Cron-Ueberfaelligkeit, Capabilities des REST-Users, Health) | **`wordpress_rest_request`** auf `openclaw-helper/v1/*` **wenn** MU-Helfer auf der Site installiert ist | WP-CLI/`exec` auf dem Gateway (wenn erlaubt) – siehe [MU_HELPER.md](MU_HELPER.md) |
| Composer, npm, git, Docker, systemd | **`exec`** | — |
| UI ohne API (Customizer, manche Plugins) | **`browser`** (nur mit klarer Nutzerfreigabe fuer Schreibaktionen) | — |
| Lokaler Entwicklungs-Code im Workspace | Workspace-**read** / **write** / **edit** | — |

## Hinweise

- **Plugin-Tools** brauchen Eintrag in `tools.allow` (oder Plugin-Bundle-Name), siehe [CONNECTING.md](CONNECTING.md). In **sandboxed** Setups reicht die globale Allowlist allein oft nicht; Sandbox-Policy und `group:openclaw` siehe [OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md).
- **Secrets** nie in Chat oder Git; [AUTH.md](AUTH.md).
- **Browser** ist langsamer und fragiler als REST/WP-CLI – nur wenn noetig.

Siehe auch [TOOLING.md](TOOLING.md) (Entscheidungsbaum).
