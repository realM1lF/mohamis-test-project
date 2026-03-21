# OpenClaw Plugin: WordPress Site Tools

Registers **optional** agent tools for use with the **`wordpress-site-ops`** skill.

**Nur dieses Repo geklont?** Relative Pfade zu `../openclaw-wordpress-skill/` gelten nicht – siehe **[STANDALONE.md](STANDALONE.md)**. Im Monorepo: Skill unter `../openclaw-wordpress-skill/`.

| Tool | Purpose |
|------|---------|
| **`wordpress_connection_check`** | REST discovery + optional auth probe + optional `wp core version` (no secrets in output). |
| **`wordpress_rest_request`** | WordPress REST API via `fetch` + Application Password (Basic). |
| **`wordpress_wp_cli`** | WP-CLI via `wp` or `ddev wp` (no shell), allowlisted prefixes + global blocklist. |
| **`wordpress_media_upload`** | Multipart `POST wp/v2/media` for a local file under `process.cwd()` (max 25 MiB). |
| **`wordpress_plugin_files`** | List, read, or write files only under `wp-content/plugins/<pluginSlug>/` relative to `WORDPRESS_PATH` / `wordpressPath` (no `..`, size caps). |

## Connecting an existing WordPress site

No WordPress plugin from this repository is **required** on the WP side for REST/WP-CLI. **Optional:** the skill bundles a small **MU helper** PHP file ([bundled/mu-plugin](../openclaw-wordpress-skill/bundled/mu-plugin/)) you can copy to `wp-content/mu-plugins/` for an extra REST status route. Use HTTPS, **Application Passwords**, and OpenClaw configuration as documented in the skill:

- **[CONNECTING.md](../openclaw-wordpress-skill/references/CONNECTING.md)** – topologies (REST-only vs REST+WP-CLI on the gateway host), `openclaw.json`, `tools.allow`, verification (see [OpenClaw Skills](https://docs.openclaw.ai/tools/skills), [Agent Tools](https://docs.openclaw.ai/plugins/agent-tools)).
- **[WPCLI_PRESETS.md](../openclaw-wordpress-skill/references/WPCLI_PRESETS.md)** – `wpCliProfile` presets or copy-paste `wpCliAllowPrefixes` for `plugins.entries.wordpress-site-tools.config`.
- **[DDEV.md](../openclaw-wordpress-skill/references/DDEV.md)** – local DDEV: REST URL + `wpCliRunner` / `WORDPRESS_WP_CLI_RUNNER`.

## Install

From the machine that runs the OpenClaw gateway:

```bash
cd /path/to/openclaw-wordpress-tools
npm install
openclaw plugins install /path/to/openclaw-wordpress-tools
# or symlink dev copy:
# openclaw plugins install -l /path/to/openclaw-wordpress-tools
openclaw plugins enable wordpress-site-tools
openclaw gateway restart
```

**Repo-Klon (Skill + Plugin in einem Rutsch):** nur im Monorepo: [`scripts/sync-openclaw-wordpress.sh`](../scripts/sync-openclaw-wordpress.sh) (Symlink Skill + `plugins install -l` fuer das Plugin).

## Standalone: nur dieses Repo (eigenes Git)

Oeffentliches Repository: **[github.com/realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool)** (SSH: `git@github.com:realM1lF/openclaw-wordpress-tool.git`). Sinnvoll, wenn Nutzer den Skill **nur** von ClawHub installieren.

- **WordPress / OpenClaw-Anbindung:** steht im Skill **`wordpress-site-ops`** (nach `clawhub install …` im Workspace unter `skills/wordpress-site-ops/references/`, u. a. `CONNECTING.md`). Auf ClawHub die Skill-Seite verlinken, sobald veroeffentlicht.
- **Plugin installieren:** wie oben **Install** (`npm install`, `openclaw plugins install`, `enable`, `gateway restart`) mit dem Klon **dieses** Repos (`openclaw-wordpress-tool`).
- **Maintainer** (Monorepo + Publish): [CLAWHUB_PUBLISH.md](../docs/openclaw-wordpress/CLAWHUB_PUBLISH.md) (nur bei Klon des Repos `personal-ki-agents`; sonst dieselbe Datei auf GitHub unter `docs/openclaw-wordpress/`).

## Allow the tools

All tools use **`optional: true`**. Add them to your allowlist, for example in `~/.openclaw/openclaw.json` (JSON5):

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
    // or enable every tool from this plugin:
    // allow: ["wordpress-site-tools"],
  },
}
```

Or under `agents.list[].tools.allow` for a single agent.

## Configuration

**Environment** (aligned with the skill; see `openclaw-wordpress-skill/references/AUTH.md`):

| Variable | Purpose |
|----------|---------|
| `WORDPRESS_SITE_URL` | Site base URL (no trailing slash) – REST tool |
| `WORDPRESS_USER` | WordPress username – REST tool |
| `WORDPRESS_APPLICATION_PASSWORD` | Application password – REST tool |
| `WORDPRESS_PATH` | **`cwd`** for WP-CLI: WordPress root for direct `wp`, or **DDEV project root** (folder with `.ddev/`) when using `ddev` runner |
| `WORDPRESS_WP_CLI_RUNNER` | Optional: `wp` (default) or `ddev` – overrides plugin config `wpCliRunner` |

Optional **plugin config** (`plugins.entries.wordpress-site-tools.config`):

- `baseUrl`, `user`, `applicationPassword` – REST overrides
- `wordpressPath` – overrides `WORDPRESS_PATH`
- `wpCliRunner` – `wp` (default) or `ddev` (see [DDEV.md](../openclaw-wordpress-skill/references/DDEV.md))
- `wpCliProfile` – when `wpCliAllowPrefixes` is **empty or omitted**, use a **named preset**: `builtin-default`, `extended-read`, `content-staging`, `staging-admin`, `dev-local` (see skill `references/WPCLI_PRESETS.md`)
- `wpCliAllowPrefixes` – if **non-empty**, **replaces** both defaults and `wpCliProfile` (array of strings, each a token prefix after `wp`, e.g. `"post list"`, `"plugin activate"`)

## Tool: `wordpress_connection_check`

- **`includeWpCli`**: optional boolean – if omitted, defaults to **true** when `WORDPRESS_PATH` or config `wordpressPath` is set, else **false**
- **REST:** unauthenticated `GET` on `…/wp-json/`; if user + application password are set, `GET wp/v2/users/me` with Basic auth
- **WP-CLI:** when enabled and path valid, runs `wp core version` or `ddev wp core version` per `wpCliRunner` / `WORDPRESS_WP_CLI_RUNNER` (separate from `wordpress_wp_cli` allowlist; fixed argv only)
- **Output:** status lines only; never prints passwords

## Tool: `wordpress_media_upload`

- **`sourcePath`**: path to a file on the **gateway host**; resolved with `path.resolve(process.cwd(), sourcePath)` and must lie **under** `process.cwd()` after `realpath` (prevents arbitrary file reads outside the workspace). Max **25 MiB**.
- **Auth:** same as `wordpress_rest_request` (Application Password Basic).
- **Endpoint:** `POST /wp-json/wp/v2/media` with multipart field `file`.

## Tool: `wordpress_rest_request`

- **`method`**: `GET` | `POST` | `PUT` | `PATCH` | `DELETE`
- **`path`**: REST path under `/wp-json`, e.g. `wp/v2/posts` or `wc/v3/products` (no `..`, no full URL)
- **`query`**: optional string map for query parameters
- **`body`**: optional JSON string for `POST` / `PUT` / `PATCH`

## Tool: `wordpress_wp_cli`

- **`args`**: array of strings – arguments **after** `wp` (do not include `wp` itself), e.g. `["core", "version"]` or `["post", "list", "--post_type=page"]`
- **Working directory**: `WORDPRESS_PATH` or config `wordpressPath` (required) – for **DDEV**, use the project root containing `.ddev/`, not only `web/`
- **Runner**: `wp` (default) or `ddev` via config `wpCliRunner` or env `WORDPRESS_WP_CLI_RUNNER` – `ddev` must be on the gateway host `PATH`
- **Allowlist**: command must start with one of the configured prefixes. Resolution: non-empty `wpCliAllowPrefixes` **replaces** everything; else `wpCliProfile` selects a built-in preset; else **default** read-heavy prefixes (`core version`, `core is-installed`, `post list`, …). Invalid `wpCliProfile` values are rejected at tool runtime.
- **Global blocklist** (always denied, even if in allowlist): first token `eval`, `eval-file`, `shell`, `cli`; `db` with second token `query`, `reset`, `clean`, `import`, `export`
- **Limits**: no shell; args must match a safe character set; max arg length 512, max 64 args; 120s timeout; combined stdout/stderr truncated at ~512 KiB

## Tool: `wordpress_plugin_files`

- **Requires** `WORDPRESS_PATH` or config `wordpressPath` pointing at the WordPress root on the **gateway host** (same as WP-CLI cwd).
- **`operation`**: `list` | `read` | `write`
- **`pluginSlug`**: directory name under `wp-content/plugins/` (lowercase, hyphens; regex `^[a-z0-9][a-z0-9-]{0,63}$`)
- **`relativePath`**: path inside that plugin directory; use `""` or `.` for list at plugin root. No `..` segments.
- **`write`**: requires `content` (UTF-8); max **512 KiB** per write. Set `overwrite: true` to replace an existing file; creates parent directories under the plugin folder as needed.
- **`read`**: max file size **2 MiB** returned.
- **Security**: resolved paths must stay under `wp-content/plugins/<pluginSlug>/`; no traversal.

## Requirements

- **OpenClaw** `>= 2026.3.0` (peer dependency)
- Node with global **`fetch`** (Node 18+)
- **`wp`** on `PATH` for direct mode, or **`ddev`** on `PATH` when `wpCliRunner` / `WORDPRESS_WP_CLI_RUNNER` is `ddev`

Per [OpenClaw – Building Plugins](https://docs.openclaw.ai/plugins/building-plugins), plugin **development** in the OpenClaw repo context may target **Node ≥ 22**; your gateway runtime can differ.

## See also

- [OPENCLAW_INTEGRATION.md](../openclaw-wordpress-skill/references/OPENCLAW_INTEGRATION.md) – OpenClaw tool/sandbox policy, allowlists, official doc links (for this skill + plugin)
- [OpenClaw – Building Plugins](https://docs.openclaw.ai/plugins/building-plugins)
- [OpenClaw – Agent Tools](https://docs.openclaw.ai/plugins/agent-tools)
