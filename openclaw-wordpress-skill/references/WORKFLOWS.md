# Arbeitsabläufe (OpenClaw / Shell / REST)

Arbeitsregeln fuer Agenten: Shell, REST oder Browser – konsistent und nachvollziehbar.

## Immer zuerst: frische Daten

- **Stale-Data-Schutz:** Vor jeder schreibenden Aktion aktuellen Stand holen (z. B. `wp post get <id>`, REST `GET` auf Ressource, oder Datei erneut lesen).
- **Eine Quelle der Wahrheit:** Antworten zu IDs, Titeln, Status nur aus **letztem Kommando-Output / API-JSON** – nicht aus Chat-Gedächtnis ergänzen.

## Read → Plan → Write → Verify

1. **Read:** Bestehende Posts/Plugins/Optionen/Dateien auslesen.
2. **Plan:** Bei mehreren Schritten oder riskanten Änderungen kurz den Plan nennen; bei einfachen Lesevorgängen direkt ausführen.
3. **Write:** Änderung ausführen (WP-CLI, `curl` PATCH/POST, oder kontrollierter Browser-Schritt).
4. **Verify (Read-after-Write):**  
   - Nach Dateiänderungen: Datei erneut lesen oder `wp plugin verify` / Syntaxcheck wenn verfügbar.  
   - Nach REST-Schreiben: `GET` derselben Ressource.  
   - PHP-Fehler im Log der Site prüfen, falls Zugriff besteht.  
   - Erst danach „erledigt“ melden.

## Komplexität

- Einfach (1–2 Schritte): direkt umsetzen.
- Komplex (viele Dateien/Systeme): Plan zeigen, Zwischenstände nach 2–3 Schritten.
- **Nicht** eigenmächtig Features ergänzen, die nicht angefragt wurden.

## Debugging (minimal invasiv)

1. Fehlerlog / `wp option` / relevante Datei lesen.  
2. Ursache benennen.  
3. **Kleinsten** Fix anwenden – nicht komplett neu schreiben ohne Grund.

## Beiträge vs. Seiten

Immer anhand der **aktuellen Nutzeranfrage** unterscheiden – nie verwechseln.
