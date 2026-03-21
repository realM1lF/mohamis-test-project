# Plugin-Entwicklung unter OpenClaw (Playbook)

Kuratierte Leitplanken fuer **eigene** Plugins und **Addon-Plugins** (nicht Fremdcode patchen). **Tiefe** kommt vom [WordPress Developer Handbook](https://developer.wordpress.org/) und den [Coding Standards](https://developer.wordpress.org/coding-standards/) – hier: Reihenfolge, Sicherheit und OpenClaw-spezifische Umsetzung.

**Wann laden:** Bei Aufgaben mit **PHP/JS unter `wp-content/plugins/`** oder **eigenen REST-Routen** – zusammen mit `{baseDir}/references/DOMAIN.md` und `{baseDir}/references/WORKFLOWS.md`.

## OpenClaw vs. In-WordPress-Agent

`wordpress-site-tools` bietet **kein** `patch_plugin_file` / dediziertes grep-Tool. Arbeitablauf:

- **Lesen:** Workspace-Dateien oder `wordpress_wp_cli` / `exec` nur im Allowlist-Rahmen; ggf. `wordpress_rest_request` fuer Daten auf der Site.
- **Aendern:** Gezieltes Edit im **Workspace** (oder synchronisiertem Plugin-Ordner); **immer vollstaendige Datei gelesen** bevor grossflaechig ueberschrieben wird (Analog „patch vs. write“: bestehende Dateien nicht blind komplett ersetzen ohne Read).
- **Pruefen:** Read-after-Write, `wordpress_connection_check` bei Konfig-Themen, PHP-Log nur wenn Zugriff erlaubt und sicher.

**VERBOTEN als Strategie:** Beliebiges PHP auf dem Server ausfuehren, nur um Woo/Content zu aendern – stattdessen **REST** (`wc/v3`, …) oder **WP-CLI** mit passendem `wpCliProfile` ([WPCLI_PRESETS.md](WPCLI_PRESETS.md)).

## Architektur: Hooks

- **Actions** (`do_action`): Ereignisse; Callbacks ohne Rueckgabewert-Erwartung fuer den Kern.
- **Filters** (`apply_filters`): Werte transformieren; immer **return** des (ggf. geaenderten) Werts.
- **Prioritaet:** Standard 10; Reihenfolge bei gleicher Prioritaet = Registrierungsreihenfolge.
- **Startpunkt:** Eigenes Plugin: Hauptdatei mit Plugin-Header, `ABSPATH`-Check, dann typisch `plugins_loaded` oder frueher nur wenn noetig (Constants).
- **Admin:** `admin_menu`, `admin_init` fuer Settings; immer **Capabilities** pruefen (`current_user_can`).

Handbuecher: [Plugin API / Hooks](https://developer.wordpress.org/plugins/hooks/), [Actions](https://developer.wordpress.org/reference/functions/add_action/), [Filters](https://developer.wordpress.org/reference/functions/add_filter/).

## Eigene REST-API

- `register_rest_route` mit Namespace und Route; **immer** `permission_callback` (nie `__return_true` fuer schreibende/sensible Daten ohne Konzept).
- Argumente validieren (`validate_callback`); Ausgaben **escapen** je nach Kontext.
- Siehe [REST API](https://developer.wordpress.org/rest-api/).

## Sicherheit und Daten

- **Nonces** fuer Admin-Formulare und AJAX; **Capabilities** statt nur „eingeloggt“.
- **Sanitize** bei Input, **Escape** bei Output (`esc_html`, `esc_attr`, `wp_kses_post`, … je nach Kontext).
- **Prepared Statements** fuer $wpdb; keine String-Konkatenation fuer SQL mit Nutzerdaten.
- **Prefix** fuer Optionen, Meta-Keys, Funktionsnamen (Konflikte vermeiden).

## Lifecycle und Struktur

- **Activation/Deactivation:** `register_activation_hook` / `register_deactivation_hook`; bei CPT **Rewrite:** `flush_rewrite_rules` in Activation/Deactivation ([DOMAIN.md](DOMAIN.md)).
- **uninstall.php:** Cleanup bei echten Tabellen/Options; nicht nur leere Datei vergessen.
- **i18n:** Textdomain, `load_plugin_textdomain`; Strings uebersetzbar halten – [Internationalization](https://developer.wordpress.org/plugins/internationalization/).
- Dateien **> ca. 300 Zeilen** teilen (Lesbarkeit, Reviews).

## Scaffold-Checkliste (Orientierung)

Als Ergaenzung zur Tabelle in [DOMAIN.md](DOMAIN.md) – optionale „Features“ beim Anlegen eines Plugins:

| Feature-Idee | Typische Bausteine |
|--------------|-------------------|
| Admin-Einstellungen | Settings API oder eigene Options-Seite, Capability, Nonce |
| Frontend-CSS/JS | `wp_enqueue_style` / `wp_enqueue_script`, `filemtime` fuer Version |
| REST-Endpunkte | eigene Datei, `rest_api_init`, `permission_callback` |
| Woo-nah | `Requires Plugins: woocommerce`, Dependency-Check, HPOS-Kompatibilitaet deklarieren wo noetig ([WOO_ELEMENTOR.md](WOO_ELEMENTOR.md)) |
| Elementor-nah | `Requires Plugins: elementor`, Mindestversion pruefen ([WOO_ELEMENTOR.md](WOO_ELEMENTOR.md)) |

## Qualitaet (lokal beim Nutzer)

- **WPCS / PHPCS:** [Coding Standards](https://developer.wordpress.org/coding-standards/wordpress-coding-standards/) – im Projekt als Dev-Dependency einrichten; der Skill **fuehrt** PHPCS nicht aus.
- **POT-Datei:** `wp i18n make-pot` (WP-CLI, wenn im Preset erlaubt).
- **Tests:** PHPUnit-Setup optional; fuer Aenderungen: Read-after-Write ([WORKFLOWS.md](WORKFLOWS.md)) und projektinterne manuelle Tests (Maintainer-Doku im Quell-Repository).

## Fremd-Plugins erweitern

- **Addon-Plugin** mit Hooks/Filtern der Doku des Ziel-Plugins; **kein** dauerhaftes Editieren von Vendor-Dateien.
- Siehe [USER_EXPECTATIONS.md](USER_EXPECTATIONS.md) §2.1.

## Typische PHP-Fallen (Kurz)

| Falle | Hinweis |
|-------|---------|
| `the_content()` im `the_content`-Filter | Endlosschleife moeglich – Parameter `$content` nutzen |
| `is_cart()` auf Block-Cart-Seiten | kann false sein – Seiten-ID mit Woo-Funktionen pruefen |
| Meta-Keys raten | immer aus speicherndem Code uebernehmen |
| `wp_redirect()` nach Output | Headers already sent – frueh redirecten + `exit` |
| Block-Frontend | viel UI clientseitig – nicht nur PHP-Template erwarten |

## Canonical Links (Sammlung)

- [Plugin Handbook](https://developer.wordpress.org/plugins/)
- [REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Coding Standards](https://developer.wordpress.org/coding-standards/)
- [Security](https://developer.wordpress.org/apis/security/)

**Optionaler MU-Helfer auf der Site:** Quelltext im Skill unter `bundled/mu-plugin/` – Deploy nach `wp-content/mu-plugins/`. Dient **Betrieb und Diagnose** (REST `openclaw-helper/v1/status`, `/health`, `/me/capabilities`) – **nicht** zum Generieren oder Deployen von Plugin-Code aus dem Chat; Entwicklungsworkflow bleibt Workspace/WP-CLI/Datei-Tools. Wann sinnvoll: [MU_HELPER.md](MU_HELPER.md); Routen: [bundled/mu-plugin/README.md](../bundled/mu-plugin/README.md).
