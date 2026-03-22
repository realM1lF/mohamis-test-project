# OpenClaw Plugin: WordPress Site Tools

## New here?

**What is this?** An **OpenClaw plugin** (manifest ID **`wordpress-site-tools`**) for the machine that runs your **OpenClaw gateway**. It registers **optional agent tools** so an AI agent can work with an **existing WordPress site**: e.g. **REST** (posts, media, WooCommerce, …) and optionally **WP-CLI**, with allowlists and no shell passthrough where it matters for safety.

**Which skill does it belong to?** The agent skill **`wordpress-expert`** (often installed from **ClawHub**). That skill holds **instructions, playbooks, and docs** (`CONNECTING`, auth, DDEV, …). **This repo** is only the **plugin that implements the tools**—without it, the WordPress tools are not available in the gateway. Typical order: install the skill → clone **this** repo, `npm install`, `openclaw plugins install` → configure the site (Application Passwords, etc.) using the skill’s **`CONNECTING.md`** in your workspace at `skills/wordpress-expert/references/`.

**Cloned only this repo?** Relative paths like `../openclaw-wordpress-skill/` do not exist—see **[STANDALONE.md](STANDALONE.md)**. In the monorepo, the skill lives under `../openclaw-wordpress-skill/`.

## Identifiers (ClawHub vs OpenClaw)

| What | Value | Used for |
|------|--------|----------|
| **ClawHub skill slug** (skill key) | `wordpress-expert` | `clawhub install wordpress-expert` (or your ClawHub CLI equivalent); workspace path `skills/wordpress-expert/` |
| **OpenClaw plugin id** | `wordpress-site-tools` | `openclaw plugins enable wordpress-site-tools`; `plugins.entries.wordpress-site-tools` in `openclaw.json` |
| **Standalone plugin GitHub repo** | [realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool) | Clone the **plugin** only (repo name ends in `-tool`, singular) |
| **Monorepo folder** (this tree) | `openclaw-wordpress-tools/` | Only when you work inside the **personal-ki-agents** repository |

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

## Typical setup (ClawHub skill + this plugin)

1. On the **OpenClaw gateway** host, install the **skill** from **ClawHub**, e.g. **`clawhub install wordpress-expert`** (or whatever your ClawHub version documents—see [ClawHub](https://docs.openclaw.ai/tools/clawhub) and [Skills](https://docs.openclaw.ai/tools/skills)).
2. **Clone this plugin** (standalone: [github.com/realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool)), then follow **[Install](#install)** above (`npm install`, `openclaw plugins install`, `openclaw plugins enable wordpress-site-tools`, `openclaw gateway restart`).
3. Configure WordPress (HTTPS, Application Passwords) and **`openclaw.json`** using the skill’s references—start with **`CONNECTING.md`** under `skills/wordpress-expert/references/` after the skill is installed.

**Monorepo:** If you develop inside **[personal-ki-agents](https://github.com/realM1lF/personal-ki-agents)** (or your fork), you can use [`scripts/sync-openclaw-wordpress.sh`](../scripts/sync-openclaw-wordpress.sh) to symlink the skill and link-install this plugin in one step.

## Standalone clone (plugin-only Git repo)

Canonical plugin repository: **[github.com/realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool)** · SSH: `git@github.com:realM1lF/openclaw-wordpress-tool.git`

Use this when you install **`wordpress-expert`** from **ClawHub** but want the **plugin source** from GitHub. Relative links to `../openclaw-wordpress-skill/` in this README only work in the **monorepo** checkout—if you cloned **only** the plugin repo, read **[STANDALONE.md](STANDALONE.md)** for where skill files live on disk and official **OpenClaw** / **ClawHub** links.

**Maintainers** (publish skill vs plugin, export script): [docs/openclaw-wordpress/CLAWHUB_PUBLISH.md](../docs/openclaw-wordpress/CLAWHUB_PUBLISH.md) when you have the full **personal-ki-agents** tree; the same file is also published under `docs/openclaw-wordpress/` on the standalone plugin GitHub repo.

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
