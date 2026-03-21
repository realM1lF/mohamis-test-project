# Sicherheit und Defaults

Sicherheit und Defaults fuer WordPress-Arbeit ueber OpenClaw (Host).

## Destruktive Aktionen

Hier gibt es keine fest eingebauten PHP-Tools – alles laeuft ueber Shell/HTTP/Browser. Deshalb gilt:

- Befehle wie Plugin- oder Theme-Loeschen, erzwungenes Post-Loeschen, rekursives rm, Datenbank-Drops: nur nach expliziter Nutzeranweisung. Bei Unsicherheit nachfragen.
- Vor Loeschen oder Theme-Wechsel: aktuellen Stand dokumentieren; Backup empfehlen.

## Safety-Defaults

- Neue Posts und Seiten: bevorzugt als Draft, ausser der Nutzer will veroeffentlichen.
- Plugins: nur aus wordpress.org oder bekannten Quellen.
- Den aktuellen Admin-Account nie loeschen oder sperren.
- Keine direkten Raw-DB-Aenderungen ohne klare Anweisung und Rollback-Plan.

## Globale WordPress-Einstellungen

Nicht als Nebeneffekt aendern, nur auf explizite Anfrage: blogname, blogdescription, show_on_front, page_on_front, page_for_posts, permalink_structure, default_role, users_can_register, template, stylesheet.

Bei WP-CLI: keine Bulk-option update ohne Bestaetigung.

## Injection

Niemals ungefilterten Nutzertext in Shell-Befehle einbauen. Nutze feste Subcommands und sichere Quoting-Regeln.

OpenClaw Sandbox und Elevated-Policies beachten: https://docs.openclaw.ai/gateway/security

## Fremd-Code

Drittanbieter-Plugins nicht direkt patchen. Eigene Plugins oder Child-Themes bevorzugen.

## Umgebung und Profile

- **Staging vs. Produktion:** Breite WP-CLI-Presets (`staging-admin`, `dev-local`) und schreibende REST-Calls nur mit **Staging**-Zielen und klarem Rollback/Backup kombinieren – nicht dieselben Zugangsdaten und Rechte wie fuer reine Lese-Profile mischen.
- **Konkrete JSON-Muster:** [CONNECTING.md](CONNECTING.md) Abschnitt „Betriebsprofile“.
- **Plugin-Entwicklung:** Regeln und Checklisten: [PLUGIN_DEV_PLAYBOOK.md](PLUGIN_DEV_PLAYBOOK.md).

## Kritische Settings

Read, Change, Verify. Nur fertig melden, wenn die Verifikation stimmt.

## Kommunikation

Optional: freundlich, per Du, ein Emoji ist erlaubt; im Chat kurz halten (Token sparen).
