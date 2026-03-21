# WordPress an OpenClaw anbinden (bestehende Installation)

Anleitung fuer **bestehende** WordPress-Sites: kein zusaetzliches WordPress-Plugin aus diesem Repo noetig. Anbindung ueber **HTTPS + Application Password** (REST) und optional **WP-CLI** auf demselben Rechner wie der **OpenClaw-Gateway**.

OpenClaw: [Skills](https://docs.openclaw.ai/tools/skills), [Skills config](https://docs.openclaw.ai/tools/skills-config), [Building Plugins](https://docs.openclaw.ai/plugins/building-plugins), [Agent Tools](https://docs.openclaw.ai/plugins/agent-tools).

---

## 1. Zwei gueltige Topologien

| Topologie | Wann | `WORDPRESS_SITE_URL` + App-Password | `WORDPRESS_PATH` / WP-CLI-Tool |
|-----------|------|--------------------------------------|--------------------------------|
| **A – REST nur remote** | Shared Hosting, Gateway woanders, kein FS-Zugriff auf WP | **Ja** | **Nein** (Tool `wordpress_wp_cli` ungenutzt oder leer) |
| **B – REST + WP-CLI** | Gateway auf Host **mit** gleichem Dateisystem wie WP (oder Mount) | **Ja** | **Ja** – Ordner, in dem `wp core version` laeuft |

`WORDPRESS_PATH` ist das **cwd** fuer `wp` auf dem **Gateway-Host**, keine URL. Ohne Server-Zugriff: nur **REST**.

**DDEV (lokal):** REST mit `https://<projekt>.ddev.site`; fuer WP-CLI im Plugin `wpCliRunner: "ddev"` und `WORDPRESS_PATH` = DDEV-**Projektroot** (mit `.ddev/`). Details: [DDEV.md](DDEV.md).

---

## 2. WordPress-Seite (einmalig)

1. **HTTPS**
2. Benutzer mit passender Rolle
3. **Application Password:** Benutzer – Profil – Application Passwords – neu anlegen, sicher speichern (nicht das Login-Passwort)
4. **REST testen:** Browser `https://ihre-domain.tld/wp-json/` (Unterverzeichnis: `https://domain.tld/blog/wp-json/`)
5. Security-/Firewall-Plugins pruefen, wenn REST blockiert

`WORDPRESS_SITE_URL` = oeffentliche Basis-URL **ohne** trailing slash.

---

## 3. OpenClaw-Gateway

**Wichtig fuer Tools:** Plugin-Tools und Aenderungen an `tools.allow` / `plugins.allow` werden im **Gateway-Prozess** registriert. Nach solchen Aenderungen: **`openclaw gateway restart`**. Ein **neuer Chat (`/new`)** ist **kein Ersatz** dafuer; `/new` hoechstens nutzen, wenn nach Restart die **Oberflaeche** noch eine veraltete Tool-Liste zeigt.

### 3.1 Skill

```bash
cp -r /pfad/zu/openclaw-wordpress-skill ~/.openclaw/workspace/skills/wordpress-site-ops
```

Danach **`openclaw gateway restart`**, dann pruefen: `openclaw skills list --eligible`. Optional neuer Chat, falls die UI den Skill nicht anzeigt.

**Skill von ClawHub:** Wenn du den Skill mit der ClawHub-CLI installiert hast, enthaelt das Bundle **nur** Anweisungen und `bundled/` – **nicht** das OpenClaw-Plugin. Plugin **`wordpress-site-tools`** separat installieren – oeffentliches Repo: **[github.com/realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool)** (oder lokaler Pfad / Monorepo-Klon; siehe Skill-README).

### 3.2 Plugin

**Variante A – nur Plugin klonen (empfohlen mit Skill von ClawHub):**

```bash
git clone https://github.com/realM1lF/openclaw-wordpress-tool.git
cd openclaw-wordpress-tool && npm install
openclaw plugins install -l "$(pwd)"
openclaw plugins enable wordpress-site-tools
openclaw gateway restart
```

**Variante B – Monorepo** `personal-ki-agents`, Ordner `openclaw-wordpress-tools/`:

```bash
cd /pfad/zu/openclaw-wordpress-tools && npm install
openclaw plugins install /pfad/zu/openclaw-wordpress-tools
openclaw plugins enable wordpress-site-tools
openclaw gateway restart
```

### 3.3 Plugin-ID und `plugins.allow`

- **Manifest-ID** (in `openclaw.plugin.json`): **`wordpress-site-tools`**. Unter `plugins.entries` muss der Schluessel **genau so** lauten: `plugins.entries.wordpress-site-tools` – nicht nach NPM-Paket- oder Ordnernamen raten.
- OpenClaw kann **warnen**, wenn **`plugins.allow`** leer ist und Plugins aus Workspace/Pfad geladen werden. Optional eintragen:

```json5
plugins: {
  allow: ["wordpress-site-tools"],
```

**Hinweis:** Ist `plugins.allow` **nicht leer**, sind je nach OpenClaw-Version typischerweise nur noch **gelistete** Plugin-IDs aktiv/erlaubt – andere Plugins dann **zusaetzlich** in dieselbe Liste aufnehmen.

### 3.4 Agent-Tools erlauben (`tools.allow`)

Die WordPress-Tools sind **optional** und brauchen eine **Tool-Allowlist** ([Agent Tools](https://docs.openclaw.ai/plugins/agent-tools)):

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
  },
}
```

Kurzform: `tools.allow: ["wordpress-site-tools"]` (alle Tools dieses Plugins).

### 3.5 `openclaw.json` Beispiel (Skill + Plugin + Secrets)

```json5
{
  skills: {
    entries: {
      "wordpress-site-ops": {
        enabled: true,
        env: {
          WORDPRESS_SITE_URL: "https://ihre-site.tld",
          WORDPRESS_USER: "wp_user",
          WORDPRESS_APPLICATION_PASSWORD: "xxxx xxxx xxxx xxxx xxxx xxxx",
          // WORDPRESS_PATH: "/var/www/html",
        },
      },
    },
  },
  plugins: {
    allow: ["wordpress-site-tools"],
    entries: {
      "wordpress-site-tools": {
        enabled: true,
        config: {
          // wordpressPath: "/var/www/html",
          // wpCliRunner: "ddev", // nur fuer DDEV: Projektroot mit .ddev/; siehe DDEV.md
          // wpCliAllowPrefixes: siehe WPCLI_PRESETS.md
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

### 3.6 OpenClaw: Policy, Sandbox, Gruppen, Provider

Globales **`tools.allow`/`tools.deny`** (Deny gewinnt), **`group:openclaw`** ohne Plugin-Tools, **Sandbox**-Allowlists (`tools.sandbox.tools.*`), **`tools.byProvider`**, Env **Host vs. Container**: siehe **[OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md)** (mit Links zur offiziellen OpenClaw-Doku).

**Sandbox:** Env, ausfuehrbare Dateien (`wp`, `curl`) und **zusaetzliche** Tool-Allowlists fuer sandboxed Sessions: **[OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md)**; Kurz auch [Skills config](https://docs.openclaw.ai/tools/skills-config).

### 3.7 Optionales MU-Plugin (im Skill gebundelt)

Im Skill liegt **`bundled/mu-plugin/openclaw-site-helper.php`** (siehe [bundled/mu-plugin/README.md](../bundled/mu-plugin/README.md)). Das ist **WordPress-PHP** – kein OpenClaw-Gateway-Code.

- **Auf die Site bringen:** Datei nach **`wp-content/mu-plugins/`** kopieren (Gateway braucht **Dateizugriff** auf die Installation, oder ihr deployt manuell).
- **Routen (alle per `wordpress_rest_request`, `path` ohne `wp-json/`):**
  - `GET openclaw-helper/v1/status` – Kurzinfo inkl. `features`-Liste (User mit **`manage_options`**)
  - `GET openclaw-helper/v1/health` – Laufzeit/Diagnose aus WP-Sicht (**`manage_options`**)
  - `GET openclaw-helper/v1/me/capabilities` – Rechte des **aktuellen** App-Password-Users; optional Query `check=cap1,cap2` (**eingeloggt**)
- **Topologie:** Bei **REST-only** oder **Sandbox ohne Shell** besonders sinnvoll; bei **DDEV + WP-CLI** optional (Komfort). Kein Ersatz fuer **`wordpress_plugin_files`** – siehe **[MU_HELPER.md](MU_HELPER.md)**.

### 3.8 Optionales Tool: Plugin-Dateien auf dem Host (`wordpress_plugin_files`)

Wenn **`WORDPRESS_PATH`** (oder `wordpressPath`) auf dem **Gateway-Host** auf die WordPress-Installation zeigt, koennt ihr **`wordpress_plugin_files`** in **`tools.allow`** aufnehmen: list/read/write **nur** unter `wp-content/plugins/<pluginSlug>/` (kein `..`, Groessenlimits). Nach Plugin-Update: **`openclaw gateway restart`**. Sandbox: ggf. `tools.sandbox.tools.allow` – siehe [OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md).

---

## 4. Verifikation

**Empfohlen (Plugin):** Wenn **`wordpress_connection_check`** in `tools.allow` ist, zuerst dieses Tool ausfuehren: es prueft anonym `GET wp-json/`, mit Application Password `GET wp/v2/users/me`, und optional `wp core version` bzw. `ddev wp core version` (wenn `wpCliRunner` / `WORDPRESS_WP_CLI_RUNNER` und `WORDPRESS_PATH` / `wordpressPath` gesetzt). Keine Secrets im Tool-Output.

Zusaetzlich manuell moeglich:

```bash
curl -sS -u "USER:APP_PASSWORD" "https://ihre-site.tld/wp-json/wp/v2/posts?per_page=1"
```

Topologie B:

```bash
cd /pfad/zur/wp-installation && wp core version
```

---

## 5. Mehrwert Plugin vs. nur Skill

| | Nur Skill + exec/curl | Mit wordpress-site-tools |
|--|----------------------|---------------------------|
| REST | Shell-Strings, Quote-Risiko | `wordpress_rest_request`, nur wp-json-Pfad |
| WP-CLI | freies `wp` | `wordpress_wp_cli`, Allowlist + Blocklist, kein Shell |
| Erstkontakt / Diagnose | manuell curl / wp | `wordpress_connection_check`, weniger Trial-and-Error |

---

## 6. Betriebsprofile (Empfehlung)

Gleiche OpenClaw-Mechanismen: `tools.allow` / `tools.deny`, optional `tools.profile`, Sandbox laut [OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md). **`tools.deny` gewinnt.**

**Ziel:** Lesen, Content, Staging/Admin und Dev trennen – keine Produktions-Credentials mit breiten WP-CLI-Rechten mischen ([SAFETY.md](SAFETY.md)).

- **read-only:** `wpCliProfile` `builtin-default` oder `extended-read`; nur lesende REST/WP-CLI.
- **content:** `content-staging` – redaktionelle Aufgaben laut [WPCLI_PRESETS.md](WPCLI_PRESETS.md).
- **staging-admin:** `staging-admin` – mehr Plugin-/CLI auf **Staging**.
- **dev-local:** `dev-local` – nur lokale Umgebung; Bundle `wordpress-site-tools` nur wenn noetig.

In **sandboxed** Sessions: WordPress-Tool-Namen ggf. in `tools.sandbox.tools.allow` wiederholen; Env unter `agents.defaults.sandbox.docker.env`.

Beispiel-Ausschnitt (JSON5, `wpCliProfile` in Plugin-Config):

```json5
plugins: {
  entries: {
    "wordpress-site-tools": {
      enabled: true,
      config: { wpCliProfile: "content-staging" },
    },
  },
},
tools: {
  allow: [
    "wordpress_connection_check",
    "wordpress_rest_request",
    "wordpress_wp_cli",
  ],
},
```

---

## 7. Links

- [AUTH.md](AUTH.md)
- [WPCLI_PRESETS.md](WPCLI_PRESETS.md)
- [PLUGIN_DEV_PLAYBOOK.md](PLUGIN_DEV_PLAYBOOK.md)
- [Plugin README](../../openclaw-wordpress-tools/README.md)
