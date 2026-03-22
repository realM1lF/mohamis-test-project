# Standalone clone (plugin repository only)

**Canonical plugin repo:** [github.com/realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool)

If you cloned **only** this repository (not the **personal-ki-agents** monorepo), **relative links** in [README.md](README.md) that point to `../openclaw-wordpress-skill/` **do not exist** on disk. Use **ClawHub** + your OpenClaw workspace for skill documentation instead.

Official ecosystem docs: [ClawHub](https://docs.openclaw.ai/tools/clawhub), [OpenClaw Skills](https://docs.openclaw.ai/tools/skills), [Agent Tools](https://docs.openclaw.ai/plugins/agent-tools), [Building Plugins](https://docs.openclaw.ai/plugins/building-plugins).

## Skill documentation (`wordpress-expert`)

On **ClawHub**, the skill slug is **`wordpress-expert`**. Install it with your CLI (for example **`clawhub install wordpress-expert`**—see current ClawHub docs if the command differs).

After installation, reference files on the gateway typically live under:

`skills/wordpress-expert/references/`

Key files:

| Topic | File in skill workspace |
|-------|-------------------------|
| Connection, topologies, verification | `CONNECTING.md` |
| Auth, env, secrets | `AUTH.md` |
| DDEV | `DDEV.md` |
| WP-CLI allowlist presets | `WPCLI_PRESETS.md` |

See also identifiers in [README.md](README.md) (**ClawHub** skill slug vs **OpenClaw** plugin id **`wordpress-site-tools`**).

## Optional MU helper on the WordPress site

The small PHP helper lives in the **skill** tree under `bundled/mu-plugin/` (not in this plugin-only repo). After installing **`wordpress-expert`**, copy files from `skills/wordpress-expert/bundled/mu-plugin/` into your site’s `wp-content/mu-plugins/` (details in the skill’s `MU_HELPER.md` / bundled README).

## Maintainers: export from the monorepo

If you develop in the parent repo **personal-ki-agents** and publish **this** plugin to GitHub separately, use **`scripts/export-openclaw-wordpress-tools-for-github.sh`** and **`docs/openclaw-wordpress/CLAWHUB_PUBLISH.md`** from that monorepo. A standalone clone of **openclaw-wordpress-tool** does not include those paths unless you copy the published docs from GitHub.
