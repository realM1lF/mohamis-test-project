# MU-Helfer (`openclaw-site-helper`): wann nutzen?

Das **Must-Use-Plugin** im Skill unter [bundled/mu-plugin/](../bundled/mu-plugin/) registriert **eigene** REST-Routen unter **`openclaw-helper/v1`**. Es laeuft **in WordPress-PHP** auf der **Ziel-Site** – nicht im OpenClaw-Gateway.

**Technische Referenz** (Routen, Permissions, Beispiele): [bundled/mu-plugin/README.md](../bundled/mu-plugin/README.md).

---

## Entscheidungsmatrix

| Setup | MU-Helfer |
|-------|-----------|
| **REST-only** (nur `wordpress_rest_request`, kein SSH/`exec`/`wp` auf dem Server) | **Hoher Mehrwert** – Health- und Runtime-Daten aus Sicht von WordPress; Capabilities genau fuer den **Application-Password-User** |
| **Sandbox** ohne Shell oder ohne `wp`/`curl` im Container, REST aber erlaubt | **Hoher Mehrwert** – Diagnose ohne WP-CLI |
| **Shared Hosting** – REST mit App-Password, kein CLI | **Sinnvoll** |
| **Lokal DDEV** mit `wordpress_wp_cli` und/oder `exec` | **Optional** – viele Infos auch per `wp`/`php`; MU spart trotzdem **einen** konsolidierten REST-Call (z. B. Health) |
| **Plugin-Dateien** unter `wp-content/plugins/<slug>/` lesen/schreiben | **Nicht** ueber MU – Tool **`wordpress_plugin_files`** (Gateway braucht `WORDPRESS_PATH`) oder Workspace/Deploy |

---

## Konkrete Trigger (Agent)

**Routen nutzen**, wenn das MU-Plugin auf der Site **installiert** ist (sonst 404) und mindestens eines zutrifft:

1. Du sollst pruefen, ob der **konfigurierte Application-Password-User** bestimmte Rechte hat → **`GET .../me/capabilities`** (optional `check=install_plugins,...`).
2. Du brauchst **PHP-Extensions / Memory / Cron-Ueberfaelligkeit / Upload-Verzeichnis beschreibbar** aus Sicht der **laufenden** Site → **`GET .../health`** (erfordert `manage_options` fuer diesen User).
3. Du willst schnell **Helper-Version + welche Endpunkte aktiv sind** → **`GET .../status`** (`features`-Array).

**Standard-WordPress-REST** (`wp/v2/...`, Woo `wc/v3/...`) immer **zuerst** fuer Content/Shop – der Helfer ist **kein** Ersatz dafuer.

---

## Anti-Patterns

- **„MU ist nutzlos“** pauschal sagen, obwohl nur **REST** erlaubt ist – dann ist Health/Capabilities oft der **einzige** saubere Weg ohne Shell.
- **Lokal alles per WP-CLI** – MU ist dann **Komfort**, kein Muss; fair kommunizieren.
- **Datei-IO im Plugin-Verzeichnis** ueber eigene MU-REST-Endpunkte erfinden – stattdessen **`wordpress_plugin_files`** / WP-CLI / Workspace laut [NATIVE_VS_PLUGIN.md](NATIVE_VS_PLUGIN.md).

---

## Installation

Deploy von [openclaw-site-helper.php](../bundled/mu-plugin/openclaw-site-helper.php) nach **`wp-content/mu-plugins/`** – siehe [bundled/mu-plugin/README.md](../bundled/mu-plugin/README.md) und [CONNECTING.md](CONNECTING.md) §3.7.

---

## Optional (spaeter)

OpenClaw-Plugin **`wordpress_connection_check`** koennte optional pruefen, ob `openclaw-helper/v1/status` erreichbar ist („Helfer installiert?“) – derzeit nicht im Pflichtumfang des Skills; siehe Repo `openclaw-wordpress-tools`.
