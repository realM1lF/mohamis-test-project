# WooCommerce und Elementor

Hinweise fuer OpenClaw mit **REST**, **WP-CLI** oder **Browser** – ohne spezielle In-WordPress-Agent-Tools.

## WooCommerce

- Produkt-/Bestell-/Gutschein-Logik über **WooCommerce APIs** (REST `wc/v3` wo möglich) statt ad-hoc-PHP in fremden Plugins.
- **OpenClaw:** `wordpress_rest_request` mit Pfad unter `wc/v3/...` bevorzugen; WP-CLI nur mit passendem **`wpCliProfile`** ([WPCLI_PRESETS.md](WPCLI_PRESETS.md)). Kein beliebiges PHP auf dem Server als Ersatz für Shop-CRUD.
- **Variable Produkte (Reihenfolge):** Produkt anlegen (`variable`) → Attribute setzen → Variationen erzeugen → per GET/List prüfen (REST oder erlaubtes WP-CLI).
- **Eigenes Woo-nahes Plugin:** Im Plugin-Header `Requires Plugins: woocommerce`; Admin-Notice wenn Woo fehlt. **HPOS:** Kompatibilität mit Custom Order Tables laut [Woo-Doku](https://woocommerce.com/document/high-performance-order-storage/) deklarieren, wenn ihr Order-Plugins anfasst.
- Keine „Shortcut“-Hacks, die Shop-Daten umgehen – CRUD über die offizielle Schicht.

Wenn REST nicht reicht: gezielt **Admin-Oberfläche** (Browser) oder ein **kleines eigenes Plugin** – nicht fremde Plugin-Dateien editieren. Scaffold-Hinweise: [PLUGIN_DEV_PLAYBOOK.md](PLUGIN_DEV_PLAYBOOK.md).

## Elementor

- **Eigenes Elementor-nahes Plugin:** `Requires Plugins: elementor` im Header; Mindestversion z. B. mit `defined('ELEMENTOR_VERSION')` und `version_compare` prüfen; bei fehlendem Elementor Admin-Notice.
- **Bestehende** Elementor-Seiten: Struktur verstehen, dann gezielt ändern (über Editor, Exporte oder Site-spezifische APIs – je nach Zugriff).
- **Kein professionelles Design von Null:** Nutzer auf Template-Kits / Designer hinweisen; du passt Inhalte/Struktur an.
- Echte **Elementor-Widgets** nutzen, kein rohes HTML im Text-Widget als Ersatz für Widgets.
- Vor Layoutänderungen: aktuelle Struktur/Seitenlayout einlesen (Stale-Data-Schutz).
- Neue Elementor-Seiten bevorzugt als **Draft**.
- Container-Modell (verschachtelte Container) statt veraltetes Section/Column wo applicable.
- Bei Tool-/API-Fehlern: **kein** stilles HTML-Fallback – Fehler melden.
- **Frontend prüfen:** Nach sichtbaren Änderungen betroffene URL laden (Browser oder erlaubter HTTP-Zugriff) – nicht nur „Code geschrieben“.

## Grenzen

Spezialisierte **In-WordPress**-Hilfsfunktionen (z. B. dedizierte Admin-Tools) gibt es hier nicht. Entscheide anhand von [TOOLING.md](TOOLING.md), ob REST, WP-CLI, Browser oder ein **eigenes kleines Plugin** auf der Site nötig ist.

Geplante Verbesserung: eigene OpenClaw-Tools (Fortschritt im Quell-Repository der Maintainer).
