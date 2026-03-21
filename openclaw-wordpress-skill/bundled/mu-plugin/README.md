# OpenClaw Site Helper (Must-Use Plugin)

PHP-Quelltext fuer **WordPress**, nicht fuer den OpenClaw-Gateway. Wird mit dem Skill **mitgeliefert**, muss auf der **Ziel-Site** liegen, damit die REST-Routen existieren.

**Nur Skill von ClawHub:** Dort liegt oft **nur** diese README (Text) – **keine** `.php`-Datei, weil ClawHub keine Nicht-Textdateien im Bundle will. Die Datei **`openclaw-site-helper.php`** holst du aus dem **vollstaendigen** Git-Repository (Ordner `openclaw-wordpress-skill/bundled/mu-plugin/` im Projekt-Klon).

Fuer **wann** sich Installation lohnt und **Abgrenzung** zu WP-CLI / `wordpress_plugin_files`: siehe [references/MU_HELPER.md](../../references/MU_HELPER.md).

## Installation

1. Datei **`openclaw-site-helper.php`** nach **`wp-content/mu-plugins/`** kopieren (oder Symlink). Ordner `mu-plugins/` anlegen, falls er fehlt.
2. MU-Plugins laden automatisch – kein Aktivieren im Plugin-Menue noetig.
3. **Voraussetzung:** Der OpenClaw-Gateway muss **Schreibzugriff** auf diese Verzeichnisse haben **oder** ihr kopiert manuell (FTP, Deploy, Hosting-Panel).

## REST-Uebersicht

**Namespace:** `openclaw-helper/v1` (in `wordpress_rest_request` als `path` **ohne** `wp-json/`-Praefix angeben, z. B. `openclaw-helper/v1/status`).

| Methode | Pfad | Permission | Zweck |
|---------|------|------------|--------|
| GET | `openclaw-helper/v1/status` | `manage_options` | Kurzinfo: Helper-Version, `features`-Liste, WP-/PHP-Version, `site_url` |
| GET | `openclaw-helper/v1/health` | `manage_options` | Site-Laufzeit: Memory, Extensions (Whitelist), Cron-Ueberfaelligkeit (begrenzt gezaehlt), Upload-Verzeichnis beschreibbar?, Locale, Zeitzone – **keine** Plugin-Liste, keine Pfade zu `wp-config` |
| GET | `openclaw-helper/v1/me/capabilities` | eingeloggter REST-Nutzer | Alle **wahren** Capabilities des **aktuellen** Nutzers (Application Password); optional Query `check=cap1,cap2` fuer Ja/Nein-Map |

**Authentifizierung:** Wie ueblich per Application Password / Session gegen `WORDPRESS_SITE_URL` (siehe [references/AUTH.md](../../references/AUTH.md)).

### Beispiele (`wordpress_rest_request`)

- **Status:** `method: GET`, `path: openclaw-helper/v1/status`
- **Health:** `method: GET`, `path: openclaw-helper/v1/health`
- **Capabilities:** `method: GET`, `path: openclaw-helper/v1/me/capabilities`
- **Capabilities mit Check:** `method: GET`, `path: openclaw-helper/v1/me/capabilities`, `query: { check: "install_plugins,edit_themes" }`

## Wann installieren? (Kurz)

| Szenario | Empfehlung |
|----------|------------|
| Nur REST vom Gateway, kein `exec` / kein WP-CLI auf dem Ziel | **Sinnvoll** – Health/Capabilities aus WP-Sicht |
| Strikte Sandbox ohne Shell | **Sinnvoll** fuer Diagnose mit `wordpress_rest_request` |
| Lokal DDEV + `wordpress_wp_cli` / `exec` | **Optional** (Komfort, ein Call statt mehrerer Shell-Schritte) |
| Dateien unter `wp-content/plugins/<slug>/` lesen/schreiben | **Nicht** ueber dieses MU-Plugin – Tool **`wordpress_plugin_files`** (mit `WORDPRESS_PATH`) oder Deploy/Workspace; siehe unten |

## Was bewusst nicht enthalten ist

- **Kein** generisches Datei-Read/Write unter `wp-content/plugins/...` ueber diese REST-API (Doppelung zu **`wordpress_plugin_files`**, hoeheres Risiko).
- **Keine** Secrets, keine vollstaendige Plugin-Liste, keine sensiblen `wp_options`-Dump.

## Sicherheit

Minimale, dokumentierte Felder. Routen mit `manage_options` nur fuer Admin-App-Passwords bzw. entsprechende Konten. `/me/capabilities` zeigt nur die Rechte des **angemeldeten** Nutzers – fuer least-privilege-Tests mit **nicht-Admin**-Application-Password nutzbar.

Bei Bedarf Datei entfernen oder `permission_callback` in einer lokalen Fork anpassen (nicht aus dem Skill-Sync ueberschreiben).

## Version

Aktuell im Plugin-Header und Konstante `OPENCLAW_SITE_HELPER_VERSION` in `openclaw-site-helper.php` (z. B. `0.2.0`). Nach Updates auf der Site: gleiche Datei erneut deployen.

## Ausblick

Weitere **lesende** Routen nur bei klarer betrieblicher Luecke; siehe [references/MU_HELPER.md](../../references/MU_HELPER.md).
