# WordPress-Domänenwissen (kompakt)

Kompakte **Checklisten** fuer WP-CLI, REST und manuelle Entwicklung unter `wp-content`.

Fuer **Plugin-Architektur, Sicherheit, REST-Routen, WPCS-Links und OpenClaw-Workflow:** [PLUGIN_DEV_PLAYBOOK.md](PLUGIN_DEV_PLAYBOOK.md).

## Dokumentation

Fuer Tiefe: offizielle Handbuecher zu Block Editor, REST, Hooks, WP-CLI; WooCommerce- und Elementor-Doku bei Shop/Builder-Themen.

## REST

- Discovery: `GET /wp-json/` bzw. `GET /wp-json/wp/v2/` für Namespaces.
- WooCommerce Admin-API oft unter Namespace `wc/v3` (Auth beachten).

## Plugin-Scaffolds (manuell oder generiert)

Wenn du neue Plugins anlegst, orientiere dich an:

| Typ | Wesentliche Punkte |
|-----|---------------------|
| **plain** | Standard-Plugin-Header, `plugins_loaded`, eigener Prefix |
| **block** | `block.json`, Editor-Script-Pflicht für Inserter, `index.asset.php`-Dependencies vollständig (`wp-blocks`, `wp-element`, …); `render.php` mit `get_block_wrapper_attributes()` |
| **custom-post-type** | CPT registrieren, Taxonomien vor CPT, Rewrite, `flush_rewrite_rules` in Activation, `uninstall.php` |
| **shortcode** | `shortcode_atts()`, Output-Buffering, bedingtes `wp_enqueue_style` |
| **woocommerce / elementor** | `Requires Plugins` im Header, Dependency-Checks im Admin |

**Optionale „Features“** beim Scaffold (eigene Dateien/Ordner): Admin-Settings (Settings API o. a.), Frontend-CSS/JS (`wp_enqueue_*`), eigene REST-Dateien unter `rest_api_init` – siehe Playbook.

Features wie Admin-Settings, `rest-api`, Frontend-Assets als eigene Dateien auslagern; Dateien **>300 Zeilen** teilen.

## Datenbank in eigenen Plugins

Tabellen nicht nur im Activation-Hook anlegen (Race beim ersten Schreiben). Stattdessen: `admin_init` + Options-Version + `dbDelta`; `uninstall.php` mit `DROP TABLE` + `delete_option`.

## CSS / Frontend

- Theme-**CSS-Variablen** bevorzugen (Block-Theme: `--wp--preset--*`).  
- Kein Inline-CSS im Frontend-Output; `wp_enqueue_style` + `filemtime()` für Cache-Busting.  
- Vor größeren Style-Änderungen: bestehende Styles der Site inspizieren (eigene Site per REST/HTML, kein Credential-Leak).

## Häufige Fehler

- Unvollständige Klammern, inkonsistente Variablennamen, fehlende Edge Cases (null/leer).  
- Nach jeder Dateiänderung: **Inhalt erneut lesen** bevor „fertig“.

## z-index

Moderate Werte (oft 1–10), nicht eskalieren.

## WooCommerce-Block-Cart (Kurz)

- Block-Cart ≠ klassischer Shortcode: `is_cart()` kann beim Enqueue unzuverlässig sein – Seiten-ID von `wc_get_page_id('cart')` prüfen.  
- Klassische Template-Hooks greifen am Block-Cart oft nicht – Slots/Store-API/`render_block` prüfen.  
- `WC()->cart` in eigenen REST-Callbacks oft nicht verfügbar – Daten serverseitig beim Frontend-Request holen oder Store-API erweitern.

Details bei Bedarf: WordPress Developer Resources, WooCommerce REST-Dokumentation, Elementor Developer Docs.
