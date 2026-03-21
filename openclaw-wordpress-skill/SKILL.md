---
name: wordpress-site-ops
description: "WordPress-Sites betreiben (Content, Plugins, Themes, WooCommerce) und Plugin-/Theme-Code unter wp-content (siehe references/PLUGIN_DEV_PLAYBOOK.md) via Plugin-Tools (wordpress_connection_check, wordpress_rest_request, wordpress_wp_cli, optional wordpress_media_upload, optional wordpress_plugin_files) oder Fallback exec/curl/Browser/Workspace. Optional MU-Helfer auf der Site (bundled/mu-plugin): REST openclaw-helper/v1/status, health, me/capabilities – wann sinnvoll siehe references/MU_HELPER.md. Nutze diesen Skill bei WP-, Woo- oder Elementor-Aufgaben auf einer erreichbaren Installation."
metadata: {"openclaw":{"skillKey":"wordpress-site-ops","requires":{"anyBins":["wp","curl"]}}}
---

# WordPress Site Ops

## Wann aktiv

Bei Aufgaben zu **WordPress**: Beitraege/Seiten, Medien, Plugins, Themes, WooCommerce, Elementor, REST, Code unter `wp-content`. Sonst nicht erzwingen.

## Immer

1. Frische Daten vor Schreibzugriff (Stale-Data-Schutz).
2. Fakten nur aus **letztem Terminal- oder API-Output** – nicht aus Chat ergaenzen.
3. Keine Secrets in Antworten oder Git; siehe `{baseDir}/references/AUTH.md`.
4. Schreibende Shell-Befehle: **kein** Rohtext aus Nutzereingaben ohne Escaping/Quotes.
5. **REST:** Wenn **`wordpress_rest_request`** (Plugin **`wordpress-site-tools`**, in `tools.allow`) verfuegbar ist, **bevorzugen** statt frei zusammengebautem `curl` – Credentials wie in `{baseDir}/references/AUTH.md`. Sonst REST ueber Shell/`curl` laut TOOLING.
6. **WP-CLI:** Wenn **`wordpress_wp_cli`** erlaubt ist und **`WORDPRESS_PATH`** (oder Plugin-Config) gesetzt ist, **bevorzugen** statt freiem `exec wp` – Allowlist/Blocklist im Plugin; Umfang ueber **`wpCliProfile`** (Preset) oder explizites **`wpCliAllowPrefixes`**. Sonst WP-CLI wie in TOOLING ueber **`exec`** mit Safety-Regeln.
7. **Anbindung pruefen:** Nach Konfigurationsaenderungen oder bei Fehlern zuerst **`wordpress_connection_check`** nutzen, wenn erlaubt – siehe `{baseDir}/references/CONNECTING.md`.
8. **Medien-Upload (multipart):** Wenn **`wordpress_media_upload`** in `tools.allow` ist, fuer Datei-Uploads bevorzugen statt manuellem `curl -F`. Sonst wie in TOOLING.
8b. **Plugin-Dateien auf dem Host:** Wenn **`wordpress_plugin_files`** erlaubt ist und **`WORDPRESS_PATH`** gesetzt ist, fuer list/read/write **nur** unter `wp-content/plugins/<slug>/` dieses Tool bevorzugen statt freiem `exec` – siehe `{baseDir}/references/NATIVE_VS_PLUGIN.md` und `{baseDir}/references/CONNECTING.md` §3.8.
8c. **MU-Helfer-REST (`openclaw-helper/v1/...`):** Nur nutzen, wenn das MU-Plugin laut `{baseDir}/bundled/mu-plugin/README.md` auf der **WordPress-Site** installiert ist (sonst 404). **Bevorzugen** fuer **Inside-WP-Diagnose** und **Capabilities des Application-Password-Users** (`/health`, `/me/capabilities`, `/status`); **nicht** als Ersatz fuer Plugin-Datei-IO (`wordpress_plugin_files` / WP-CLI / Workspace). Entscheidungshilfe: `{baseDir}/references/MU_HELPER.md`.
9. **Native OpenClaw:** Shell, Browser und Workspace-Dateien **nicht** durch Plugin ersetzen – Abgrenzung in `{baseDir}/references/NATIVE_VS_PLUGIN.md`.
10. **Gateway vs. Chat-Session:** Neue oder geaenderte **Plugin-Tools** (`tools.allow`, `plugins.allow`, Plugin enable/install, Plugin-Code) brauchen typisch **`openclaw gateway restart`**, damit der Gateway sie registriert. **Nicht** pauschal behaupten, ein **neuer Chat (`/new`)** sei dafuer Pflicht. `/new` nur vorschlagen, wenn die **laufende Session** offenbar noch **keine** Plugin-Tools anbietet, obwohl der Nutzer Restart und Config schon erledigt hat (UI-/Client-Cache). Aenderungen an **Skill-Env** in `openclaw.json`: erst in der **gleichen Session** testen; wenn Tools/Env fehlen, **Restart** empfehlen. Details: `{baseDir}/references/CONNECTING.md` (Abschnitt zu Gateway).
11. **Plugin-/Theme-Entwicklung (Code unter `wp-content`):** Zuerst `{baseDir}/references/DOMAIN.md` und `{baseDir}/references/PLUGIN_DEV_PLAYBOOK.md` laden; Ablauf `{baseDir}/references/WORKFLOWS.md` (Read – Plan – Write – Verify). Woo/Elementor: `{baseDir}/references/WOO_ELEMENTOR.md`. Kein Fremd-Plugin patchen – Addon-Ansatz im Playbook.
12. **Laien:** Antworten in einfacher Sprache; technische Details (Befehle, JSON) nur auf Nachfrage oder kurz am Ende.

## Referenz (Progressive Disclosure)

Lies bei Bedarf:

- `{baseDir}/references/CONNECTING.md` – bestehende WP-Instanz an OpenClaw anbinden (Topologien, openclaw.json)
- `{baseDir}/bundled/mu-plugin/README.md` – optionaler WordPress-MU-Helfer (Quelltext im Skill; Deploy auf die Site)
- `{baseDir}/references/MU_HELPER.md` – wann MU-Helfer-REST sinnvoll ist (vs. WP-CLI / `wordpress_plugin_files`)
- `{baseDir}/references/OPENCLAW_INTEGRATION.md` – OpenClaw Tool-/Sandbox-Policy, `group:*`, `deny`, offizielle Links
- `{baseDir}/references/DDEV.md` – lokale WordPress-Instanz mit DDEV (REST-URL, ddev wp / wpCliRunner)
- `{baseDir}/references/NATIVE_VS_PLUGIN.md` – wann Plugin-Tools vs. exec / Browser / Workspace
- `{baseDir}/references/WPCLI_PRESETS.md` – Allowlist-Presets (`wpCliProfile` / `wpCliAllowPrefixes`) fuer wordpress_wp_cli
- `{baseDir}/references/USER_EXPECTATIONS.md` – was Nutzer erwarten, Bedienung, Zielbild (Abgleich Entwicklung)
- `{baseDir}/references/FOR_SITE_OWNERS.md` – fuer Nutzer ohne Technik-Hintergrund
- `{baseDir}/references/OVERVIEW.md` – Index aller Referenzen
- `{baseDir}/references/TOOLING.md` – WP-CLI vs REST vs Browser
- `{baseDir}/references/AUTH.md` – URLs, Application Passwords, Env
- `{baseDir}/references/WORKFLOWS.md` – Read, Plan, Write, Verify
- `{baseDir}/references/SAFETY.md` – Defaults, riskante Optionen
- `{baseDir}/references/DOMAIN.md` – Blocks, Plugins, CPT, Fallstricke
- `{baseDir}/references/PLUGIN_DEV_PLAYBOOK.md` – Hooks, REST, Sicherheit, Scaffold, WPCS-Links (OpenClaw-Workflow)
- `{baseDir}/references/WOO_ELEMENTOR.md` – Woo und Elementor

Dieser Skill steuert **OpenClaw auf dem Host** (optionale Plugin-Tools: Verbindungscheck, REST, WP-CLI, optional Medien-Upload, optional begrenzte Plugin-Datei-IO; sonst `exec`/`curl`, Browser, Workspace) – nicht die Ausfuehrung innerhalb von WordPress-PHP.
