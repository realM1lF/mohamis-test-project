# Checkliste: Skill testen

**Repo-Klon:** Skill + Plugin per Symlink einrichten: im uebergeordneten Repo `./scripts/sync-openclaw-wordpress.sh` (optional `--restart`), siehe [README.md](../../openclaw-wordpress-skill/README.md#installation).

## Anbindung (bestehende WordPress-Instanz)

Vollstaendige Schrittfolge: [CONNECTING.md](../../openclaw-wordpress-skill/references/CONNECTING.md). Kurz:

1. WP: HTTPS, Application Password, `/wp-json/` im Browser pruefen
2. OpenClaw: Skill nach `skills/wordpress-site-ops`, Plugin installieren + `enable`
3. `openclaw.json`: `skills.entries`, `plugins.entries.wordpress-site-tools`, `tools.allow` setzen
4. **`openclaw gateway restart`** nach Allowlist-/Plugin-Aenderungen (nicht nur `/new` – siehe Skill-README „Gateway vs. Chat“)
5. `curl`-REST-Test und ggf. `wp core version` (Topologie B)
6. Chat-Test mit harmloser Leseanfrage (Plugin-Tools direkt versuchen; `/new` nur bei veralteter Tool-Liste in der UI)

Allowlist-Presets: [WPCLI_PRESETS.md](../../openclaw-wordpress-skill/references/WPCLI_PRESETS.md). DDEV lokal: [DDEV.md](../../openclaw-wordpress-skill/references/DDEV.md).

**Tools „blocked by sandbox“ / fehlen trotz `tools.allow`:** [OPENCLAW_INTEGRATION.md](../../openclaw-wordpress-skill/references/OPENCLAW_INTEGRATION.md) lesen; CLI: `openclaw sandbox explain`.

**Regression / Release:** Feste Testfaelle: [TEST_MATRIX.md](TEST_MATRIX.md). Vor Release: [RELEASE.md](RELEASE.md).

---

## skills-ref validate (AgentSkills)

Der Validator vergleicht den **Ordnernamen** mit dem Feld **`name`** in `SKILL.md` (`wordpress-site-ops`). Deshalb **nicht** gegen den Repo-Ordner `openclaw-wordpress-skill` validieren.

**Zielpfad (empfohlen):** nach Sync wie im README – z. B. `~/.openclaw/workspace/skills/wordpress-site-ops` (oder `echo $OPENCLAW_WORKSPACE/skills/wordpress-site-ops`).

```bash
# CLI: Paket agentskills/skills-ref (z. B. ohne globale Installation)
npx --yes skills-ref validate /ABSOLUTER/PFAD/zu/wordpress-site-ops
```

**Alternativ** lokal im Repo-Klon (Ordner muss `wordpress-site-ops` heissen):

```bash
mkdir -p /pfad/zu/personal-ki-agents/.skills-ref-tmp
rm -rf /pfad/zu/personal-ki-agents/.skills-ref-tmp/wordpress-site-ops
cp -a /pfad/zu/personal-ki-agents/openclaw-wordpress-skill \
  /pfad/zu/personal-ki-agents/.skills-ref-tmp/wordpress-site-ops
cd /pfad/zu/personal-ki-agents/.skills-ref-tmp
npx --yes skills-ref validate wordpress-site-ops
```

Bei Fehlern: Frontmatter, fehlende Dateien, verbotene Zeichen im `name` – fixen, erneut validieren. Vor **ClawHub-Publish** sollte die Validierung gruen sein.

---

Nach Installation des Skills nach `~/.openclaw/workspace/skills/wordpress-site-ops/`:

1. `openclaw skills list` – Skill sichtbar
2. `openclaw skills list --eligible` – nur wenn `wp` oder `curl` auf PATH (Host/Container)
3. `openclaw skills info wordpress-site-ops` – Metadata und Pfade
4. `openclaw skills check` – Gateway-Diagnose
5. Eine harmlose Anfrage (nur Lesen), z. B. REST `GET` auf `/wp-json/` oder `wp option get blogname`

## Plugin `wordpress-site-tools` (optional)

Nach [README.md](../../openclaw-wordpress-skill/README.md#plugin-wordpress-site-tools-optional):

1. `cd …/openclaw-wordpress-tools && npm install`
2. `openclaw plugins install <pfad>` und `openclaw plugins enable wordpress-site-tools`
3. `tools.allow` (und ggf. `plugins.allow`) setzen, dann **`openclaw gateway restart`** – noetig fuer Tool-Registrierung; **`/new` ersetzt das nicht** (nur bei veralteter UI-Tool-Liste sinnvoll)
4. `openclaw plugins doctor` – keine Plugin-Fehler
5. Optional: `wordpress_connection_check` (Erstkontakt)
6. REST-Test: `wordpress_rest_request` mit `method: GET`, `path: wp/v2/posts`, `query: { per_page: "1" }` (nur Lesen)
7. WP-CLI-Test: `WORDPRESS_PATH` setzen; `wordpress_wp_cli` mit `args: ["core", "version"]` (muss zur Allowlist passen)
8. Optional: `wordpress_plugin_files` mit `operation: list`, `pluginSlug` eines existierenden Plugins, `relativePath: ""` (nur mit `tools.allow` und Dateizugriff)

Referenz: [agentskills skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref).
