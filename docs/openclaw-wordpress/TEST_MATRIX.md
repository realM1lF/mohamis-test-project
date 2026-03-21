# Testmatrix (Referenz-Umgebung)

Festgelegte **manuelle** Prueffaelle fuer Skill + Plugin `wordpress-site-tools`. Nach Aenderungen am Skill/Plugin oder nach Gateway-Updates mindestens die fuer eure Topologie relevanten Zeilen abarbeiten und **Umgebung** (lokal/staging, OpenClaw-Version, WP-Version) kurz notieren.

| ID | Bereich | Aktion | Erwartung |
|----|---------|--------|-----------|
| T1 | REST lesen | `wordpress_rest_request` GET `wp/v2/posts?per_page=1` | 200, JSON mit Posts oder leeres Array |
| T2 | REST Schreiben | POST Draft-Post (oder PATCH existierender Entwurf) | 201/200, `status` draft wie geplant |
| T3 | Auth | REST mit falscher App-Password oder ohne Auth auf geschuetzte Route | 401/403, keine Secrets im Chat |
| T4 | REST-Fehler | GET auf nicht existierenden Endpunkt | 404 oder WP-Fehlerobjekt, klar benennen |
| T5 | Woo (falls aktiv) | GET `wc/v3/products?per_page=1` (oder lesender Endpunkt passend zur Rolle) | 200 oder erklaerbarer Auth-Fehler |
| T6 | WP-CLI (Topologie B) | `wordpress_wp_cli` args `["core","version"]` | Versionsstring, keine Shell |
| T7 | Verbindung | `wordpress_connection_check` (wenn erlaubt) | Statuszeilen ohne Passwoerter |
| T8 | Medien (optional) | `wordpress_media_upload` mit kleiner Testdatei unter Gateway-cwd | 201 oder klare Fehlermeldung |
| T9 | Sandbox | Bei Docker-Session: `openclaw sandbox explain` + WordPress-Tools testen | Kein „blocked by sandbox“, wenn Policy gesetzt ([OPENCLAW_INTEGRATION.md](../../openclaw-wordpress-skill/references/OPENCLAW_INTEGRATION.md)) |
| T10 | MU-Helfer | Nach Kopie nach `mu-plugins/`: GET `openclaw-helper/v1/status` und GET `openclaw-helper/v1/health` (Admin-App-Password, `manage_options`) | 200, JSON mit `ok`, `features` enthaelt u. a. `health`; Health ohne Secrets/Pfade zu `wp-config` |
| T11 | Plugin-Dateien | `wordpress_plugin_files` list unter bekanntem `pluginSlug`, ggf. read einer kleinen Datei | Kein Pfad-Escape; Schreibtest nur auf Staging |
| T12 | MU-Helfer Capabilities | GET `openclaw-helper/v1/me/capabilities` mit demselben App-Password; optional Query `check=edit_posts,manage_options` | 200, `capabilities`-Array; `check_results` nur wenn Query gesetzt; keine fremden User-Daten |

**Hinweis:** Automatisierung (CI) ist optional; diese Matrix dient zuerst **Reproduzierbarkeit** und Maintainer-Abgleich. Siehe auch [QA.md](QA.md). MU-Routen und Topologien: [MU_HELPER.md](../../openclaw-wordpress-skill/references/MU_HELPER.md), [bundled/mu-plugin/README.md](../../openclaw-wordpress-skill/bundled/mu-plugin/README.md). Release-Abnahme: [RELEASE.md](RELEASE.md).
