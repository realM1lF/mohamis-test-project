# WordPress lokal mit DDEV + OpenClaw

DDEV startet WordPress in Containern. Der **OpenClaw-Gateway** laeuft auf deinem **Host** (Linux/macOS/WSL). Dieses Skill/Plugin ist dafuer ausgelegt.

## REST (ohne Besonderheit)

- **URL:** `https://<projektname>.ddev.site` (ohne trailing slash) → `WORDPRESS_SITE_URL`
- **Auth:** Application Password im WordPress-Benutzer wie ueblich ([AUTH.md](AUTH.md))
- **Tools:** `wordpress_rest_request`, `wordpress_connection_check`, `wordpress_media_upload` nutzen `fetch` auf dem Host. Wenn der Browser die DDEV-URL ohne Zertifikatswarnung oeffnet, funktioniert das meist auch fuer Node/OpenClaw. Bei TLS-Fehlern: DDEV-/mkcert-Doku (CA auf dem Host vertrauen) oder `NODE_EXTRA_CA_CERTS` – projektspezifisch.

## WP-CLI ueber das Plugin (`wordpress_wp_cli`)

Auf dem Host gibt es oft **kein** direktes `wp` im PATH; stattdessen **`ddev wp`** im **DDEV-Projektroot** (Ordner mit `.ddev/`).

Im Plugin:

- **`WORDPRESS_PATH`** (oder `wordpressPath` in der Config) = **absoluter Pfad zu diesem Projektroot**, nicht zwingend `web/`.
- **`wpCliRunner`:** `ddev` in `plugins.entries.wordpress-site-tools.config`, **oder** Umgebung:

```bash
export WORDPRESS_WP_CLI_RUNNER=ddev
```

`WORDPRESS_WP_CLI_RUNNER` **ueberschreibt** die Config, wenn auf `wp` oder `ddev` gesetzt.

- **`ddev`** muss auf dem **gleichen Rechner wie der OpenClaw-Gateway** installiert und im PATH sein.

Technisch: Das Plugin fuehrt `spawn("ddev", ["wp", ...args], { cwd: WORDPRESS_PATH })` aus – dieselbe Allowlist/Blocklist wie bei direktem `wp`.

## Verbindungscheck

`wordpress_connection_check` nutzt **dieselbe** Runner-Logik fuer den Schritt „WP-CLI core version“.

## Standard-Setup (Kurz)

1. DDEV-Projekt laeuft (`ddev start`).
2. `WORDPRESS_SITE_URL=https://dein-projekt.ddev.site`
3. `WORDPRESS_PATH=/absolut/pfad/zum/ddev-projektroot`
4. `WORDPRESS_WP_CLI_RUNNER=ddev` **oder** `wpCliRunner: "ddev"` in der Plugin-Config
5. Gateway neu starten nach Config-Aenderung.

Siehe auch [CONNECTING.md](CONNECTING.md), [TOOLING.md](TOOLING.md).
