# ClawHub: Skill veroeffentlichen + Plugin separat (Arbeitsteilung)

Offizielle Doku: [ClawHub](https://docs.openclaw.ai/tools/clawhub), [Skills](https://docs.openclaw.ai/tools/skills).

**Wichtig:** ClawHub laedt nur den **Skill** (`wordpress-site-ops`). Das OpenClaw-Plugin **`wordpress-site-tools`** liegt im Ordner `openclaw-wordpress-tools/` – das geht **nicht** als Skill mit; Nutzer installieren es **separat** (lokal oder aus dem **Plugin-GitHub-Repo**).

**Plugin-Repository (canonical):**

- HTTPS: `https://github.com/realM1lF/openclaw-wordpress-tool`
- SSH: `git@github.com:realM1lF/openclaw-wordpress-tool.git`

### ClawHub: nur Textdateien

Die Web-Oberflaeche / der Check meldet u. a.: **Remove non-text files** fuer `.gitignore`, `.env.example`, `openclaw-site-helper.php`. Das ist **normal** – ClawHub will offenbar ein reines Text-Bundle.

**Vorgehen:** Paket mit dem Skript bauen (entfernt diese Dateien automatisch), dann **diesen** Ordner hochladen:

```bash
cd /pfad/zu/personal-ki-agents
./scripts/package-wordpress-site-ops-for-clawhub.sh
```

Ergebnis: **`build/clawhub-publish/wordpress-site-ops`** (unter deinem Repo-Root, z. B. `personal-ki-agents/build/…`) – diesen Ordner bei ClawHub auswaehlen. Der Ordner **`build/`** ist per `.gitignore` ausgeschlossen. Die **PHP-Datei** des MU-Helfers bleibt im **Git-Repo**; Nutzer holen sie von dort (siehe [bundled/mu-plugin/README.md](../../openclaw-wordpress-skill/bundled/mu-plugin/README.md)).

---

## Was du (Maintainer) machen musst

Das laesst sich nicht automatisieren, weil **Konto + Tokens + Git-Remote** bei dir liegen:

| Schritt | Aktion |
|---------|--------|
| 1 | **ClawHub:** Account (typisch via GitHub), gemaess [clawhub.ai](https://clawhub.ai) / OpenClaw-Doku. |
| 2 | **GitHub:** Eigenes Repo fuer das Plugin – z. B. [openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool) (Root = Plugin-Dateien). |
| 3 | **Plugin pushen:** Export aus `build/openclaw-wordpress-tools-github` oder `git subtree split` (siehe „Plugin-Repo initialisieren“). |
| 4 | **Doku:** Plugin-URL in Skill/CONNECTING wie unten – bei URL-Aenderung diese Datei + [CONNECTING.md](../../openclaw-wordpress-skill/references/CONNECTING.md) anpassen. |
| 5 | **ClawHub-CLI:** `npm i -g clawhub` (oder pnpm), dann **`clawhub login`** einmalig. |
| 6 | **`clawhub publish`** mit dem Pfad zu einem Ordner namens **`wordpress-site-ops`** (siehe unten). |

Alles andere (Validierung im Repo, Skill-Texte, Checklisten) kann im **Monorepo** vorbereitet werden; **Publish** ist ein Befehl auf deinem Rechner nach Login.

---

## Was im Repo vorbereitet werden kann

- `npx --yes skills-ref validate` gegen eine Kopie/Symlink `wordpress-site-ops` (gruen vor Publish).
- Keine Secrets im Skill-Bundle pruefen ([AUTH.md](../../openclaw-wordpress-skill/references/AUTH.md), [`.env.example`](../../openclaw-wordpress-skill/.env.example)).
- SKILL.md / CONNECTING mit **Plugin-Repo-URL** (nachdem du Schritt 2–4 erledigt hast).

---

## Plugin-Repo initialisieren (einmalig)

**Empfohlen:** Sauberen Export ohne `node_modules` bauen, dort `git init` – vermeidet verschachteltes `.git` im Monorepo-Unterordner und schliesst aus, dass aus Versehen `node_modules` committed wird.

```bash
cd /pfad/zu/personal-ki-agents
./scripts/export-openclaw-wordpress-tools-for-github.sh
cd build/openclaw-wordpress-tools-github
git init
git add .
git commit -m "Initial: OpenClaw plugin wordpress-site-tools"
git remote add origin git@github.com:realM1lF/openclaw-wordpress-tool.git
git branch -M main
git push -u origin main
```

Eigenes Zielverzeichnis: `./scripts/export-openclaw-wordpress-tools-for-github.sh /pfad/zum/export`

**Alternative A – `git init` direkt in `openclaw-wordpress-tools/`:** moeglich, aber unuebersichtlich (Unterordner-Git im grossen Repo) und Fehlerrisiko bei `git add`. `.gitignore` ignoriert bereits `node_modules/` und `dist/`.

**Alternative B – weiter nur Monorepo pflegen, Plugin per History spalten:**

```bash
cd /pfad/zu/personal-ki-agents
git subtree split -P openclaw-wordpress-tools -b openclaw-wordpress-tools-split
git push git@github.com:realM1lF/openclaw-wordpress-tool.git openclaw-wordpress-tools-split:main
```

(Branch `openclaw-wordpress-tools-split` lokal loeschen wenn nicht mehr noetig: `git branch -D openclaw-wordpress-tools-split`.)

**Ziel:** Remote zeigt **nur** Plugin-Dateien im Repo-Root; Nutzer sehen u. a. [STANDALONE.md](../../openclaw-wordpress-tools/STANDALONE.md) fuer Links ohne Monorepo.

Nutzer installieren z. B.:

```bash
git clone https://github.com/realM1lF/openclaw-wordpress-tool.git
cd openclaw-wordpress-tool && npm install
openclaw plugins install -l "$(pwd)"
openclaw plugins enable wordpress-site-tools
openclaw gateway restart
```

---

## Skill-Pfad fuer ClawHub

Der **Ordnername** muss zum Feld `name` in `SKILL.md` passen: **`wordpress-site-ops`**.

**Variante A – Symlink (lokal):**

```bash
./scripts/sync-openclaw-wordpress.sh
# Pfad z. B.:
# ~/.openclaw/workspace/skills/wordpress-site-ops
```

**Variante B – Kopie nur fuer Upload:**

```bash
mkdir -p build/manual && cp -a /pfad/zu/personal-ki-agents/openclaw-wordpress-skill build/manual/wordpress-site-ops
```

---

## Validierung (vor publish)

```bash
npx --yes skills-ref validate /ABS/PFAD/zu/wordpress-site-ops
```

Erwartung: `Valid skill: wordpress-site-ops`

---

## Publish-Befehl (nach `clawhub login`)

```bash
clawhub publish /ABS/PFAD/zu/wordpress-site-ops \
  --slug wordpress-site-ops \
  --name "WordPress Site Ops" \
  --version 1.0.0 \
  --changelog "Initial publish. Plugin wordpress-site-tools: https://github.com/realM1lF/openclaw-wordpress-tool" \
  --tags latest
```

Bei Folge-Releases Changelog entsprechend anpassen.

---

## Nach dem Publish

1. **ClawHub-Seite** des Skills bookmarken; URL in [ROADMAP_RESEARCH.md](ROADMAP_RESEARCH.md) §3 eintragen.
2. **Nutzer-Hinweis:** `clawhub install wordpress-site-ops` (oder aktueller Install-Befehl laut ClawHub) **plus** Plugin: `git clone https://github.com/realM1lF/openclaw-wordpress-tool.git` wie oben.
3. Bei Skill-Updates: Version/Changelog erhoehen und erneut `clawhub publish …` mit gleichem `--slug`.

---

## Kurz: Minimal deine Klicks / Befehle

1. ClawHub-Account  
2. GitHub-Repo fuer Plugin + Push  
3. Plugin-Repo pushen + Doku-URL pruefen (diese Datei / CONNECTING)  
4. `clawhub login`  
5. `skills-ref validate` + `clawhub publish` (Zeilen oben)
