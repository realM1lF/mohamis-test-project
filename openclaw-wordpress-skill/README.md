# OpenClaw Skill: wordpress-site-ops

WordPress-Betrieb aus **OpenClaw** heraus: Anweisungen und Referenzen fuer den Agenten. Ausfuehrung typischerweise ueber Plugin-Tools (**`wordpress_connection_check`**, **`wordpress_rest_request`**, **`wordpress_wp_cli`**, optional **`wordpress_media_upload`**, optional **`wordpress_plugin_files`**) wenn freigegeben; sonst **`exec`** / **`curl`** / **Browser** / Workspace – siehe [references/NATIVE_VS_PLUGIN.md](references/NATIVE_VS_PLUGIN.md).

Kompatibel mit dem [AgentSkills](https://agentskills.io/specification)-Layout (`references/`, kurzes `SKILL.md`) und [OpenClaw Skills](https://docs.openclaw.ai/tools/skills).

## WordPress anbinden (bestehende Site)

Schritt-fuer-Schritt inkl. Topologie **REST-only** vs. **REST+WP-CLI**, OpenClaw-`openclaw.json` und Verifikation: **[references/CONNECTING.md](references/CONNECTING.md)**.  
WP-CLI-Presets (`wpCliProfile` / `wpCliAllowPrefixes`): **[references/WPCLI_PRESETS.md](references/WPCLI_PRESETS.md)**.  
**OpenClaw-Policy (Sandbox, Allowlists, `group:*`, `deny`):** **[references/OPENCLAW_INTEGRATION.md](references/OPENCLAW_INTEGRATION.md)**.  
**Plugin-Entwicklung unter OpenClaw:** **[references/PLUGIN_DEV_PLAYBOOK.md](references/PLUGIN_DEV_PLAYBOOK.md)**.  
**Optionaler WordPress-MU-Helfer (PHP, zum Kopieren auf die Site):** **[bundled/mu-plugin/README.md](bundled/mu-plugin/README.md)** (Routen `openclaw-helper/v1/status`, `health`, `me/capabilities`). **Wann das sinnvoll ist:** **[references/MU_HELPER.md](references/MU_HELPER.md)**.

## Installation

### Aus dem Repo-Klon (empfohlen: ein Befehl, immer aktuell)

Im **uebergeordneten** Repo liegt [`scripts/sync-openclaw-wordpress.sh`](../scripts/sync-openclaw-wordpress.sh): verlinkt den Skill per Symlink nach `~/.openclaw/workspace/skills/wordpress-site-ops` und installiert das Plugin mit `openclaw plugins install -l` (Symlink zum Repo). Nach `git pull` einfach erneut ausfuehren.

```bash
cd /pfad/zu/personal-ki-agents
./scripts/sync-openclaw-wordpress.sh --restart
```

Anderes Workspace: `OPENCLAW_WORKSPACE=/pfad/zum/workspace ./scripts/sync-openclaw-wordpress.sh`

### Manuell (Kopie)

1. Ziel-Ordner im **aktiven Agent-Workspace** (Standard oft `~/.openclaw/workspace`):

   ```bash
   cp -r /pfad/zu/personal-ki-agents/openclaw-wordpress-skill ~/.openclaw/workspace/skills/wordpress-site-ops
   ```

   Wichtig: Der Ordnername **`wordpress-site-ops`** muss zum Feld **`name`** in `SKILL.md` passen (AgentSkills-Konvention).

2. **`openclaw gateway restart`** – damit der Gateway Skills/Plugins neu einliest. (Optional danach Chat **`/new`**, nur wenn die Oberfläche noch einen alten Stand zeigt – siehe unten.)

3. Prüfen:

   ```bash
   openclaw skills list
   openclaw skills list --eligible
   openclaw skills info wordpress-site-ops
   openclaw skills check
   ```

   CLI: [skills](https://docs.openclaw.ai/cli/skills)

### Gateway neu starten vs. neuer Chat (`/new`)

| Situation | Empfehlung |
|-----------|------------|
| `tools.allow` / `plugins.allow` geaendert, Plugin **enable**/install, Plugin-Code aktualisiert | **`openclaw gateway restart`** – sonst sind neue Tools oft noch nicht registriert. |
| Nur Skill-Ordner neu kopiert/symlink aktualisiert | Ebenfalls **Gateway restart**; dann `openclaw skills list` pruefen. |
| Env in `skills.entries…env` geaendert | Oft in **derselben Session** testen; wenn der Agent die Tools/Env nicht sieht, **Restart**. |
| Plugin-Tools fehlen trotz korrekter Config und nach Restart | **Neuer Chat (`/new`)** oder neue Web-Session – manche Clients cachen die Tool-Liste pro Thread. **Nicht** behaupten, `/new` ersetze den Restart. |

Fuer Agenten: siehe auch [SKILL.md](SKILL.md) Punkt zu Gateway vs. Session.

## Plugin: `wordpress-site-tools` (optional)

Das Repository enthaelt das OpenClaw-Plugin **[`openclaw-wordpress-tools/`](../openclaw-wordpress-tools/)** (Plugin-ID **`wordpress-site-tools`**). **Nur Skill von ClawHub?** Plugin separat: **[github.com/realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool)**. Es registriert u. a. **`wordpress_connection_check`**, **`wordpress_rest_request`**, **`wordpress_wp_cli`**, optional **`wordpress_media_upload`**, optional **`wordpress_plugin_files`** (siehe Plugin-README).

**Nur Skill von ClawHub installiert:** Das Plugin ist **nicht** im Skill-Bundle. Separat aus dem **Anbieter-Git-Repository** oder einem lokalen Klon installieren (`openclaw plugins install …`, `enable`, `tools.allow`, Gateway-Restart).

1. Im Plugin-Verzeichnis: `npm install`
2. Installieren und aktivieren:

   ```bash
   openclaw plugins install /pfad/zu/personal-ki-agents/openclaw-wordpress-tools
   openclaw plugins enable wordpress-site-tools
   openclaw gateway restart
   ```

3. Tool **freigeben** (ohne Allowlist erscheint das optionale Tool nicht), z. B. in `~/.openclaw/openclaw.json`:

   ```json5
   {
     tools: {
       allow: [
         "wordpress_connection_check",
         "wordpress_rest_request",
         "wordpress_wp_cli",
         "wordpress_media_upload",
         "wordpress_plugin_files",
       ],
       // alternativ alle Tools dieses Plugins:
       // allow: ["wordpress-site-tools"],
     },
   }
   ```

4. Env wie in [references/AUTH.md](references/AUTH.md): **`WORDPRESS_SITE_URL`**, **`WORDPRESS_USER`**, **`WORDPRESS_APPLICATION_PASSWORD`** (REST); **`WORDPRESS_PATH`** (WP-CLI-Tool, Arbeitsverzeichnis fuer `wp`). Optional Overrides unter `plugins.entries.wordpress-site-tools.config`.

Ausfuehrliche Plugin-Doku: im Monorepo `openclaw-wordpress-tools/README.md` – oder nach Klon von **[openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool)** dort `README.md`; `openclaw plugins install` mit **absolutem** Pfad zum Plugin-Ordner.

## Gating (metadata)

`SKILL.md` setzt `metadata.openclaw.requires.anyBins: ["wp","curl"]` – der Skill gilt nur als **eligible**, wenn **mindestens eines** der Binaries auf dem **Host** (bzw. im Sandbox-Container) auf `PATH` ist.

**Entscheidung (konservativ):** Beide Binaer werden beibehalten, damit **Eligibility** zu den im Skill dokumentierten **Fallbacks** passt (`curl`/`exec` fuer REST ohne Plugin-Tool, `wp` fuer WP-CLI laut [references/TOOLING.md](references/TOOLING.md)). Wer ausschliesslich REST ueber das Plugin nutzt und keine Shell-Fallbacks braucht, kann die Metadata verschmaelern und mit `openclaw skills list --eligible` pruefen.

Wenn du nur Browser nutzen willst, passe die Metadata an oder installiere zumindest `curl`.

## OpenClaw-Konfiguration (optional)

Vollstaendiger **Ausschnitt** fuer Skill + Plugin + Tool-Allowlist (Secrets nur Platzhalter; Datei typisch `~/.openclaw/openclaw.json`, JSON5):

```json5
{
  skills: {
    entries: {
      "wordpress-site-ops": {
        enabled: true,
        env: {
          WORDPRESS_SITE_URL: "https://staging.example.com",
          WORDPRESS_USER: "…",
          WORDPRESS_APPLICATION_PASSWORD: "…",
          // Nur wenn Gateway Zugriff auf WP-Dateisystem hat:
          // WORDPRESS_PATH: "/var/www/html",
        },
      },
    },
  },
  plugins: {
    entries: {
      "wordpress-site-tools": {
        enabled: true,
        config: {
          // Optional: wordpressPath, wpCliRunner ("ddev" fuer DDEV), baseUrl, wpCliProfile, wpCliAllowPrefixes – siehe WPCLI_PRESETS.md / DDEV.md
        },
      },
    },
  },
  tools: {
    allow: [
      "wordpress_connection_check",
      "wordpress_rest_request",
      "wordpress_wp_cli",
      "wordpress_media_upload",
      "wordpress_plugin_files",
    ],
  },
}
```

- Key **`wordpress-site-ops`** entspricht `metadata.openclaw.skillKey` in `SKILL.md`.
- `env` wird nur injiziert, wenn die Variable noch nicht gesetzt ist ([Skills](https://docs.openclaw.ai/tools/skills)).
- Optionale Tools des Plugins sind ohne `tools.allow` **nicht** sichtbar ([Agent Tools](https://docs.openclaw.ai/plugins/agent-tools)).
- **Sandbox:** Container erben Host-`process.env` nicht automatisch; zusaetzlich Sandbox-Tool-Allowlists beachten. Details: [references/OPENCLAW_INTEGRATION.md](references/OPENCLAW_INTEGRATION.md); Kurz: [Skills Config](https://docs.openclaw.ai/tools/skills-config).

## Lokale `.env`

Siehe [`.env.example`](.env.example). Datei `.env` nicht committen.

## Qualitätssicherung

Nach der Installation: Pruefschritte und REST/WP-CLI-Smoke-Tests in **[references/CONNECTING.md](references/CONNECTING.md)** (Verifikation).

## Maintainer (Monorepo)

ClawHub-Publish, Release-Checkliste, Testmatrix, Roadmap und `skills-ref validate`: im Git-Repository unter `docs/openclaw-wordpress/` (nicht Teil des ClawHub-Skill-Bundles).

**ClawHub-Upload:** Oberflaeche erlaubt nur Textdateien – Paket mit [`scripts/package-wordpress-site-ops-for-clawhub.sh`](../scripts/package-wordpress-site-ops-for-clawhub.sh) bauen, dann den erzeugten Ordner `wordpress-site-ops` hochladen.

**Eigenes GitHub-Repo fuer das Plugin** (`wordpress-site-tools`): [github.com/realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool) – Export/Push aus dem Monorepo: [`scripts/export-openclaw-wordpress-tools-for-github.sh`](../scripts/export-openclaw-wordpress-tools-for-github.sh), Details in `docs/openclaw-wordpress/CLAWHUB_PUBLISH.md`.

## Repo-Layout (im uebergeordneten Repository)

```
openclaw-wordpress-skill/     # dieser Skill (AgentSkills-Layout)
openclaw-wordpress-tools/     # OpenClaw-Plugin: wordpress-site-tools
docs/openclaw-wordpress/      # Maintainer: ClawHub, QA, Testmatrix, Roadmap
```

Skill-Dateien (Auszug):

```
openclaw-wordpress-skill/
├── SKILL.md
├── README.md
├── .env.example
├── .gitignore
├── bundled/mu-plugin/
└── references/
```
