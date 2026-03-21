# Nutzererwartungen: WordPress Site Ops (Skill + Tools)

Dieses Dokument beschreibt **aus Sicht einer Person**, die den **Skill `wordpress-site-ops`** und das **Plugin `wordpress-site-tools`** fuer ein WordPress-Projekt nutzen moechte: was sie **erwartet**, wie sie es **bedient**, und was **spaeter** moeglich sein soll.  

**Pflege:** Bei groesseren Aenderungen am Skill/Plugin diese Datei anpassen. Technische Follow-ups und Roadmap: Maintainer-Doku im Quell-Repository (`docs/openclaw-wordpress/`).

---

## 1. Wer bin ich als Nutzer?

Typische Rollen:

- **Website-Betreiberin / Agentur:** Ich will in **OpenClaw chatten** („Zeig die letzten Entwuerfe“, „Ist Plugin X aktiv?“, „Leg einen Draft fuer eine News-Seite an“) ohne selbst WP-Admin oder Terminal bedienen zu muessen – soweit es sicher geht.
- **Entwicklerin mit Staging:** Ich habe **OpenClaw Gateway** auf einem Rechner/Server, **WordPress** erreichbar per URL und/oder **WP-CLI** auf dem gleichen Host wie die Installation. Ich kann **Umgebungsvariablen** oder `openclaw.json` pflegen.
- **Entwicklerin + Betrieb (Zielbild):** Ich will, dass derselbe Agent **WordPress weitgehend vollstaendig bedienen** kann *und* wie ein **WordPress-Entwickler** arbeitet: **eigene Plugins** schreiben, **fremde Plugins ueber Hooks/APIs erweitern**, Struktur und Best Practices einhalten – auf Staging zuerst, mit klaren Sicherheitsgrenzen.

**Hinweis zum aktuellen Scope:** Ausfuehrung von PHP passiert in **WordPress**, nicht „im“ OpenClaw-Prozess. Der Agent entwickelt und deployt ueber **Dateizugriff** (z. B. Workspace/`exec`), **WP-CLI**, **REST** und ggf. **Git** – nicht durch einen eingebetteten PHP-Agenten im Core.

---

## 2. Was ich mir vom Produkt erwarte (hochlevel)

| Erwartung | Kurz |
|-----------|------|
| **Natuerliche Sprache** | Ich beschreibe Aufgaben auf Deutsch (oder Englisch); der Agent waehlt REST vs. WP-CLI vs. Browser laut Doku. |
| **Keine Secrets im Chat** | Passwoerter und Application Passwords liegen nur in Env / OpenClaw-Config, nicht in Prompts oder Git. |
| **Lesen vor Schreiben** | Bei Aenderungen erst aktuelle Daten holen; keine Halluzinationen ueber Stand der Site. |
| **Sicherheit** | Kein beliebiges Shell-Freifeuer; WP-CLI nur mit Allowlist, REST nur gegen konfigurierte Site. |
| **WooCommerce / Elementor** | Skill kennt Grenzen; wo APIs fehlen, wird Browser oder manuelle Schritte eingeplant. |
| **Nachvollziehbarkeit** | Ich sehe (oder kann nachfragen), *welcher* Weg genutzt wurde – Tool-Aufruf vs. curl vs. Browser. |
| **Langfrist: nahezu vollstaendige Bedienung** | Content, Medien, Plugins/Themes (aktivieren/deaktivieren), Nutzer/Rollen, viele Einstellungen – soweit REST/WP-CLI/Admin-API das hergeben; Luecken bewusst benennen (Customizer-only, spezielle Page-Builder). |
| **Langfrist: Entwickler-Rolle** | Neue Plugins (eigener Code), Anpassungen an **bestehenden** Plugins (Hooks, Filter, kompatible APIs), optional **Child Themes**; keine blinden Core-Hacks; Staging, Tests, Rollback denkbar. |

---

## 2.1 Langfrist-Zielbild: Operator *und* Entwickler

Das ist der **erweiterte Wunsch**, mit dem wir den Entwicklungsstand abgleichen (heute vs. Ziel).

### Als Operator (WordPress „fast komplett“)

- **Inhalt:** Beitraege, Seiten, Medien, Taxonomien, Menues (soweit API/CLI).
- **Erweiterungen:** Plugins und Themes **verwalten** (listen, installieren, aktivieren, updaten – mit expliziter Risiko- und Backup-Logik im Skill).
- **Shop / Builder:** Woo, Elementor etc. **soweit REST oder dokumentierte Automatisierung** reicht; sonst Browser oder klare „manuell“-Schritte.
- **Erwartung an Tools:** Breitere, **profilierbare** WP-CLI-Allowlists oder zusaetzliche sichere Tools; REST-Abdeckung wo sinnvoll; ggf. kleines **MU-Plugin** nur fuer Luecken (Health, Capabilities), nicht als Ersatz fuer saubere APIs.

### Als Entwickler (Plugins schreiben & Drittanbieter erweitern)

- **Neue Plugins:** Scaffold (Struktur, `readme.txt`, Hauptdatei, Hooks), **PHP** nach WordPress-Coding-Standards, **i18n**, **Activation/Deactivation**, eigene REST-Routen nur mit Berechtigungs-Checks.
- **Fremde Plugins erweitern:** Nur ueber **offizielle/supported** Mittel: `add_action` / `add_filter`, eigene kleine **Bridge-** oder **Addon-Plugins**, die auf dokumentierte Hooks der Ziel-Plugins setzen (Woo, ACF, etc. – je nach Projekt in Referenzen pflegen).
- **Kein Erwartungsniveau:** Fremde Plugin-Dateien direkt und dauerhaft „patchen“ ohne Update-sichere Strategie (Child/Addon bevorzugt).
- **Workflow:** Code lebt idealerweise im **Git-Workspace** oder synchronisiertem `wp-content/plugins/...`; Agent nutzt **Read – Plan – Write – Verify** ([WORKFLOWS.md](WORKFLOWS.md)); nach Deploy **aktivieren/testen** ueber WP-CLI oder REST.
- **Qualitaet:** Optional PHPCS/WP-Stubs, Tests (PHPUnit), Staging vor Produktion.

### Spannung Sicherheit vs. „komplett“

Je **mehr** der Agent schreiben darf (Dateien, DB, Plugin-Lebenzyklus), desto wichtiger sind: **Allowlists**, **Umgebungen** (nur Staging), **Bestaetigungen**, **Backups**. Das Zielbild verlangt **explizite Profile** (z. B. „nur Lesen“, „Content-Editor“, „Dev-Staging“) – heute noch nicht als fertiges Produkt umgesetzt.

---

## 3. Bedienung: Was ich heute konkret tun muss

### 3.1 Voraussetzungen

- **OpenClaw** installiert, Gateway laeuft.
- **WordPress:** HTTPS, fuer REST idealerweise **Application Passwords**; fuer WP-CLI: `wp` auf dem **gleichen System wie der Gateway** (oder vergleichbare Setup), Zugriff auf die Installationsdateien.
- Optional: `curl` und/oder `wp` auf `PATH`, damit der Skill laut Metadata **eligible** ist. Die Vorgabe bleibt **konservativ** (`anyBins: ["wp","curl"]`), damit zu den dokumentierten Shell-Fallbacks passende Umgebungen weiterhin als eligible gelten; Details: [README.md](../README.md) Abschnitt „Gating (metadata)“.

### 3.2 Installation (zwei Teile)

Die **ausfuehrliche** Anleitung fuer **bestehende** Sites (Topologie REST-only vs. REST+WP-CLI, `openclaw.json`, Verifikation): **[CONNECTING.md](CONNECTING.md)**.

Kurz:

1. **Skill** – Ordner `openclaw-wordpress-skill` nach `~/.openclaw/workspace/skills/wordpress-site-ops` kopieren (Ordnername = Skill-`name`).
2. **Plugin** – Im Ordner `openclaw-wordpress-tools`: `npm install`, dann `openclaw plugins install <pfad>`, `openclaw plugins enable wordpress-site-tools`, Gateway neu starten.
3. **Tools freigeben** – In `openclaw.json` z. B. `tools.allow` mit `wordpress_connection_check`, `wordpress_rest_request`, `wordpress_wp_cli`, optional `wordpress_media_upload`, oder `wordpress-site-tools` (OpenClaw: optionale Plugin-Tools).
4. **Konfiguration** – In `skills.entries["wordpress-site-ops"].env` (und ggf. `plugins.entries.wordpress-site-tools.config`):
   - REST: `WORDPRESS_SITE_URL`, `WORDPRESS_USER`, `WORDPRESS_APPLICATION_PASSWORD`
   - WP-CLI-Tool: `WORDPRESS_PATH` (oder `wordpressPath` in Plugin-Config)
5. **WP-CLI-Presets** – Bei Bedarf: [WPCLI_PRESETS.md](WPCLI_PRESETS.md)

Details: [README.md](../README.md), [AUTH.md](AUTH.md), `openclaw-wordpress-tools/README.md`.

### 3.3 Wie ich „bediene“

- **Chat:** Normale Anweisungen („Liste aktive Plugins“, „Hole die letzten 5 Beitraege“, „Erstelle einen Draft …“).
- **Entwicklung (heute):** Anweisungen wie „Lege unter `wp-content/plugins/mein-addon` ein Plugin an, das auf WooCommerce `woocommerce_order_status_changed` hoekt“ – der Agent nutzt dafuer typischerweise **Datei-Tools / exec** im OpenClaw-Workspace bzw. auf dem Host, **plus** Skill-Regeln ([SAFETY.md](SAFETY.md), [DOMAIN.md](DOMAIN.md)); WP-CLI-Tool unterstuetzt nur **allowlisted** Befehle.
- **Ich erwarte nicht**, dass ich Tool-Namen auswendig kenne – der Agent nutzt sie, wenn sie erlaubt und laut Skill sinnvoll sind.
- **Einschraenkung WP-CLI-Tool:** Nur Befehle, die zur **Allowlist** passen. Standard ist **lesend/konservativ**; breitere Rechte ueber **`wpCliProfile`** (Preset) oder explizites **`wpCliAllowPrefixes`** (ersetzt Profil und Defaults, wenn nicht leer).

### 3.4 Was ich heute realistisch erreichen kann

**Gut moeglich (mit passender Config):**

- Beitraege/Seiten **listen und lesen** (REST oder WP-CLI je nach Setup).
- **Plugin- und Theme-Listen** (WP-CLI mit Default-Allowlist).
- **Optionen lesen** (`option get` im Allowlist-Rahmen).
- **REST-CRUD**, soweit Rolle und Endpunkte es hergeben (Woo: z. B. `wc/v3`).
- **Plugin-Entwicklung:** PHP-/Datei-Arbeit ueber Workspace/`exec` oder **`wordpress_plugin_files`** (wenn freigegeben und `WORDPRESS_PATH` gesetzt); **Medien-Upload** zur Bibliothek ueber **`wordpress_media_upload`**, wenn freigegeben.

**Eingeschraenkt / bewusst nicht im Default-WP-CLI-Tool:**

- Beliebiges `wp post delete`, `wp plugin delete`, DB-Queries, `eval` – **nicht** ohne erweiterte Allowlist-Config bzw. REST/anderen Weg.
- Alles, was nur im **Customizer** oder in **UI-only-Plugins** geht – eher **Browser** oder manuell (Skill verweist darauf).

**Zum Zielbild „komplett + Entwickler“ (Luecke zum Ist-Stand):**

- WP-CLI-Presets: [WPCLI_PRESETS.md](WPCLI_PRESETS.md); Runtime-Auswahl im Plugin via **`wpCliProfile`** (Config + Gateway-Neustart).
- Entwickler-Playbooks: [PLUGIN_DEV_PLAYBOOK.md](PLUGIN_DEV_PLAYBOOK.md); Woo/Elementor: [WOO_ELEMENTOR.md](WOO_ELEMENTOR.md).
- Optional: zusaetzliche kontrollierte Tools statt nur generischem `exec`.
- Test- und Review: manuelle Tests nach [CONNECTING.md](CONNECTING.md); ausfuehrliche Matrix im Quell-Repository (`docs/openclaw-wordpress/TEST_MATRIX.md`); **keine** automatische CI im Skill.

---

## 4. Was ich mir fuer spaeter wuensche (Zielbild vs. Stand)

Nutzerperspektive – **Abgleich** mit technischem Stand: Maintainer-Doku `docs/openclaw-wordpress/ROADMAP_RESEARCH.md` im Quell-Repository.

| Wuensche | Stand heute (Kurz) |
|----------|---------------------|
| **Ein-Klick-Install** (ClawHub + npm-Plugin) | Skill per ClawHub moeglich; Plugin separat aus Git/Monorepo; siehe Skill-README und `docs/openclaw-wordpress/`. |
| **Breitere WP-CLI-Profile** („nur Staging“, Content, Admin, Dev) | **Presets** in [WPCLI_PRESETS.md](WPCLI_PRESETS.md); im Plugin waehlbar per **`wpCliProfile`** (ohne lange Allowlist in JSON). |
| **WordPress „nahezu komplett“ bedienen** | Teilweise (REST + begrenztes WP-CLI); schreibende/Admin-Luecken und Builder-Grenzen bleiben. |
| **Agent als Plugin-Entwickler + Erweiterer** | Ueber Workspace/exec moeglich; Skill-Referenzen erweiterbar; Medien-Upload-Tool optional; kontrolliertes Plugin-Dateischreiben weiter offen. |
| **MU-Plugin** fuer Health/Capabilities | Umgesetzt (`bundled/mu-plugin/`); optional auf der Site. |
| **Feste Testmatrix** (Posts, Draft, 401, Woo-Lese-Call) | Dokumentiert unter `docs/openclaw-wordpress/TEST_MATRIX.md` (Maintainer). |
| **Skill-Gating ohne curl**, wenn nur REST-Tool | Metadata noch `anyBins: wp,curl`; Feintuning optional. |
| **Validierung** (skills-ref) | Vor ClawHub-Publish: siehe `docs/openclaw-wordpress/QA.md`. |

---

## 5. Checkliste fuer Maintainer (Abgleich Entwicklungsstand)

Bei Release oder groesserem Feature diese Punkte kurz gegenpruefen und ggf. **Abschnitte 2.1, 3–4** oben anpassen.

- [ ] Skill installierbar wie in [README.md](../README.md) beschrieben.
- [ ] Plugin installierbar; alle Tools in Doku mit korrekten Namen (`wordpress_connection_check`, `wordpress_rest_request`, `wordpress_wp_cli`, optional `wordpress_media_upload`).
- [ ] `tools.allow` und Env-Variablen in Doku konsistent mit Code ([AUTH.md](AUTH.md), Plugin-README).
- [ ] Default-Allowlist und Blocklist fuer `wordpress_wp_cli` im Plugin-README und hier in 3.4 stimmig.
- [ ] [CONNECTING.md](CONNECTING.md) und [WPCLI_PRESETS.md](WPCLI_PRESETS.md) mit OpenClaw-Doku und Code abgeglichen.
- [ ] **Zielbild Operator+Entwickler** (Abschnitt 2.1): Luecken zu Ist-Stand in Abschnitt 3.4 / 4 aktuell halten.
- [ ] Maintainer-Roadmap (`docs/openclaw-wordpress/ROADMAP_RESEARCH.md`) reflektiert offene vs. erledigte Arbeit.
- [ ] **USER_EXPECTATIONS.md** (diese Datei): bei Scope-Aenderungen aktualisieren.

---

## 6. Verwandte Dateien

| Datei | Inhalt |
|-------|--------|
| [../README.md](../README.md) | Installation Skill + Plugin, openclaw.json-Beispiele |
| [CONNECTING.md](CONNECTING.md) | Bestehende Site anbinden, OpenClaw-Vorgaben |
| [WPCLI_PRESETS.md](WPCLI_PRESETS.md) | WP-CLI-Allowlist-Presets |
| [NATIVE_VS_PLUGIN.md](NATIVE_VS_PLUGIN.md) | Plugin-Tools vs. OpenClaw `exec` / Browser / Workspace |
| [TOOLING.md](TOOLING.md) | Reihenfolge REST vs. WP-CLI vs. Browser |
| [AUTH.md](AUTH.md) | Secrets, Env, Plugin-Overrides |
| [SAFETY.md](SAFETY.md) | Defaults, destruktive Aktionen |
| [WORKFLOWS.md](WORKFLOWS.md) | Read – Plan – Write – Verify |
| [DOMAIN.md](DOMAIN.md) | Blocks, Plugins, CPT, REST |
| [PLUGIN_DEV_PLAYBOOK.md](PLUGIN_DEV_PLAYBOOK.md) | Plugin-Entwicklung unter OpenClaw (Hooks, REST, Sicherheit) |
| `openclaw-wordpress-tools/README.md` | Plugin- und Tool-Details |

---

*Ausrichtung: Skill `wordpress-site-ops` + Plugin `wordpress-site-tools` (Verbindungscheck, REST, WP-CLI, optional Medien-Upload); langfristiges Ziel: umfassender WordPress-Betrieb und Entwickler-Rolle laut Abschnitt 2.1.*
