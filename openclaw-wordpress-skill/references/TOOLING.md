# Werkzeuge: Entscheidungsbaum

OpenClaw stellt typischerweise **`exec`** (Shell), **`browser`** und Workspace-Dateizugriff bereit – exakte Tool-Namen siehe eure Gateway-Version unter [Tools](https://docs.openclaw.ai/tools). Das Plugin **`wordpress-site-tools`** kann u. a. **`wordpress_connection_check`**, **`wordpress_rest_request`**, **`wordpress_wp_cli`**, optional **`wordpress_media_upload`** registrieren (siehe Repo-`README` / `openclaw-wordpress-tools`).

**Abgrenzung Plugin vs. nativ:** [NATIVE_VS_PLUGIN.md](NATIVE_VS_PLUGIN.md).

## Reihenfolge (Standard)

1. **WP-CLI** – in dieser Prioritaet:  
   - **a)** Agent-Tool **`wordpress_wp_cli`**, wenn installiert, in **`tools.allow`**, und **`WORDPRESS_PATH`** (oder Plugin-Config `wordpressPath`) gesetzt – Argumente als Array nach `wp`; nur erlaubte Praefixe (Defaults lesend; Preset **`wpCliProfile`** oder **`wpCliAllowPrefixes`**). Bei **DDEV:** `wpCliRunner: "ddev"` oder `WORDPRESS_WP_CLI_RUNNER=ddev`, Pfad = DDEV-Projektroot; siehe [DDEV.md](DDEV.md).  
   - **b)** Sonst **`wp`** (oder z. B. **`ddev wp`**) ueber **`exec`**, wenn verfügbar und du einen gültigen **`--path=<wp-root>`** (oder `@alias`) hast.  
   - Nie `eval` / unsichere Shell-Ketten; siehe [SAFETY.md](SAFETY.md).

2. **WordPress REST API** – in dieser Prioritaet:  
   - **a)** Agent-Tool **`wordpress_rest_request`**, wenn installiert, aktiviert und in **`tools.allow`** – Parameter `method`, `path` (unter `/wp-json`), optional `query` / `body`; Auth aus Env/Plugin-Config ([AUTH.md](AUTH.md)).  
   - **b)** **Medien-Datei hochladen:** **`wordpress_media_upload`**, wenn erlaubt (lokale Datei unter Gateway-`cwd`, siehe Plugin-README); sonst **`curl`** mit `-F` ueber **`exec`**.  
   - **c)** Sonst **`curl`** (oder aequivalent) ueber **`exec`**, wenn **`WORDPRESS_SITE_URL`** + gueltige Auth gesetzt sind.  
   - Gut für: CRUD an Inhalten, Medien-Metadaten, viele read-only Endpunkte.  
   - WooCommerce: oft Namespace `wc/v3` (App-Password oder entsprechende Rolle).

2b. **OpenClaw MU-Helfer-REST** (`openclaw-helper/v1/...`) – **nur**, wenn das MU-Plugin auf der **WordPress-Site** liegt ([bundled/mu-plugin/README.md](../bundled/mu-plugin/README.md)) und ihr die Luecke habt (REST-only, Sandbox ohne Shell, Capabilities des App-Password-Users, konsolidierte Health-Daten). **Immer zuerst** normale WP-Core-/Plugin-REST (`wp/v2`, Woo, …) fuer fachliche Aufgaben; Helfer nicht fuer Plugin-Datei-IO – siehe [MU_HELPER.md](MU_HELPER.md).

3. **Browser**, nur wenn CLI/REST nicht reichen (z. B. reiner Customizer-Flow, Plugin, das keine API hat).  
   - Fragiler und langsamer; nur mit klarer Nutzererlaubnis für schreibende Aktionen.

## Operator-Grenzen (was oft nicht oder nur teilweise automatisierbar ist)

Ohne zusaetzliche In-WordPress-Hilfsmittel (z. B. eigenes MU-Plugin) sind viele Aufgaben **nicht** sauber ueber REST oder konservatives WP-CLI loesbar:

| Bereich | Typisches Problem | Empfohlener Weg |
|---------|-------------------|-----------------|
| **Customizer** | Kein stabiler REST-Ersatz | **Browser** mit Nutzerfreigabe oder manuell |
| **Navigationsmenüs** | REST/CLI je nach Setup lueckenhaft | WP-CLI nur wenn im **Allowlist-Preset**; sonst Browser/Admin |
| **Einige Page-Builder** | Daten im Builder-Format, nicht klassische Posts | Builder-Doku, **Browser**, oder **eigenes kleines Plugin** |
| **Reine Admin-UI-Plugins** | Keine oeffentliche API | Browser oder manuell |
| **Komplexe Woo-Setup-Flows** | Teilweise nur Admin | REST `wc/v3` bevorzugen; sonst [WOO_ELEMENTOR.md](WOO_ELEMENTOR.md) |

Den Nutzer **nicht** glauben lassen, „alles“ gehe per Chat – Luecken klar benennen. Verifikation nach Installation: [CONNECTING.md](CONNECTING.md).

## Leistungsumfang

Der Agent arbeitet auf dem **Host** mit Shell, HTTP (Plugin-Tool oder Shell) und ggf. Browser – nicht als eingebetteter PHP-Agent innerhalb von WordPress.

## Sandbox (OpenClaw)

Wenn der Agent in einer **sandboxed** Session (z. B. Docker) laeuft, fehlen oft `wp` oder `curl` im Container (Host-PATH gilt nicht automatisch), und der Container erbt **nicht** automatisch `skills.entries.*.env` vom Host. Zusaetzlich gelten laut OpenClaw **eigene** Sandbox-Tool-Allowlists (`tools.sandbox.tools.allow` / `deny`) – globales `tools.allow` allein reicht dann nicht immer fuer Plugin-Tools wie `wordpress_rest_request`. Diagnose: `openclaw sandbox explain` (siehe offizielle Doku). **Details, Links und WordPress-spezifische Checkliste:** [OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md).
