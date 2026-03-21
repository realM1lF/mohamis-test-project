---
name: wordpress-site-ops
description: "Operate WordPress sites (content, plugins, themes, WooCommerce) and work on plugin/theme code under wp-content (see references/PLUGIN_DEV_PLAYBOOK.md). Works best with the companion OpenClaw plugin wordpress-site-tools (https://github.com/realM1lF/openclaw-wordpress-tool): typed tools for REST, WP-CLI, connection checks, optional media upload, and scoped plugin file access—prefer these over ad-hoc exec/curl. Without the plugin, use exec/curl/browser per references/TOOLING.md. Optional MU helper on the WordPress site (see bundled/mu-plugin/README.md; PHP source in full git repo): openclaw-helper/v1/status, health, me/capabilities—when to use: references/MU_HELPER.md. Activate for WordPress, WooCommerce, or Elementor tasks on a reachable installation."
metadata: {"openclaw":{"skillKey":"wordpress-site-ops","requires":{"anyBins":["wp","curl"]}}}
---

# WordPress Site Ops

## When to use

For tasks involving **WordPress**: posts/pages, media, plugins, themes, WooCommerce, Elementor, REST, code under `wp-content`. Do not force this skill for unrelated work.

## Always

1. Use fresh data before writes (stale-data protection).
2. State facts only from the **latest terminal or API output**—do not invent details from chat.
3. Never put secrets in replies or Git; see `{baseDir}/references/AUTH.md`.
4. For shell commands that write: **no** raw user input without escaping/quoting.
5. **REST:** If **`wordpress_rest_request`** (plugin **`wordpress-site-tools`**, listed in `tools.allow`) is available, **prefer it** over hand-built `curl`—credentials per `{baseDir}/references/AUTH.md`. Otherwise REST via shell/`curl` as in TOOLING.
6. **WP-CLI:** If **`wordpress_wp_cli`** is allowed and **`WORDPRESS_PATH`** (or plugin config) is set, **prefer it** over free-form `exec wp`—allowlist/blocklist in plugin; scope via **`wpCliProfile`** (preset) or explicit **`wpCliAllowPrefixes`**. Otherwise WP-CLI via **`exec`** with safety rules as in TOOLING.
7. **Verify connectivity:** After config changes or on errors, use **`wordpress_connection_check`** first when allowed—see `{baseDir}/references/CONNECTING.md`.
8. **Media upload (multipart):** If **`wordpress_media_upload`** is in `tools.allow`, prefer it for file uploads over manual `curl -F`. Otherwise as in TOOLING.
8b. **Plugin files on the host:** If **`wordpress_plugin_files`** is allowed and **`WORDPRESS_PATH`** is set, for list/read/write **only** under `wp-content/plugins/<slug>/` prefer this tool over free `exec`—see `{baseDir}/references/NATIVE_VS_PLUGIN.md` and `{baseDir}/references/CONNECTING.md` §3.8.
8c. **MU helper REST (`openclaw-helper/v1/...`):** Use only if the MU plugin per `{baseDir}/bundled/mu-plugin/README.md` is installed on the **WordPress site** (otherwise 404). **Prefer** for **inside-WP diagnostics** and **capabilities of the application-password user** (`/health`, `/me/capabilities`, `/status`); **not** a replacement for plugin file I/O (`wordpress_plugin_files` / WP-CLI / workspace). Decision guide: `{baseDir}/references/MU_HELPER.md`.
9. **Native OpenClaw:** Do not replace shell, browser, and workspace file access with the plugin—see `{baseDir}/references/NATIVE_VS_PLUGIN.md`.
10. **Gateway vs. chat session:** New or changed **plugin tools** (`tools.allow`, `plugins.allow`, plugin enable/install, plugin code) typically need **`openclaw gateway restart`** so the gateway registers them. **Do not** claim a **new chat (`/new`)** is always required. Suggest `/new` only if the **current session** still shows **no** plugin tools after restart and correct config (UI/client cache). For **skill env** changes in `openclaw.json`: test in the **same session** first; if tools/env are missing, recommend **restart**. Details: `{baseDir}/references/CONNECTING.md` (gateway section).
11. **Plugin/theme development (code under `wp-content`):** Load `{baseDir}/references/DOMAIN.md` and `{baseDir}/references/PLUGIN_DEV_PLAYBOOK.md` first; flow `{baseDir}/references/WORKFLOWS.md` (Read – Plan – Write – Verify). Woo/Elementor: `{baseDir}/references/WOO_ELEMENTOR.md`. Do not patch third-party plugins—addon approach in the playbook.
12. **Non-technical users:** Use plain language; technical details (commands, JSON) only on request or briefly at the end.

## Reference (progressive disclosure)

Load as needed:

- `{baseDir}/references/CONNECTING.md` – connect an existing WordPress site to OpenClaw (topologies, openclaw.json)
- `{baseDir}/bundled/mu-plugin/README.md` – optional WordPress MU helper (source in full skill repo; deploy to the site)
- `{baseDir}/references/MU_HELPER.md` – when MU helper REST makes sense (vs. WP-CLI / `wordpress_plugin_files`)
- `{baseDir}/references/OPENCLAW_INTEGRATION.md` – OpenClaw tool/sandbox policy, `group:*`, `deny`, official links
- `{baseDir}/references/DDEV.md` – local WordPress with DDEV (REST URL, ddev wp / wpCliRunner)
- `{baseDir}/references/NATIVE_VS_PLUGIN.md` – plugin tools vs. exec / browser / workspace
- `{baseDir}/references/WPCLI_PRESETS.md` – allowlist presets (`wpCliProfile` / `wpCliAllowPrefixes`) for wordpress_wp_cli
- `{baseDir}/references/USER_EXPECTATIONS.md` – user expectations, UX, target picture
- `{baseDir}/references/FOR_SITE_OWNERS.md` – for users without a technical background
- `{baseDir}/references/OVERVIEW.md` – index of all references
- `{baseDir}/references/TOOLING.md` – WP-CLI vs REST vs browser
- `{baseDir}/references/AUTH.md` – URLs, application passwords, env
- `{baseDir}/references/WORKFLOWS.md` – Read, Plan, Write, Verify
- `{baseDir}/references/SAFETY.md` – defaults, risky options
- `{baseDir}/references/DOMAIN.md` – blocks, plugins, CPT, pitfalls
- `{baseDir}/references/PLUGIN_DEV_PLAYBOOK.md` – hooks, REST, security, scaffold, WPCS links (OpenClaw workflow)
- `{baseDir}/references/WOO_ELEMENTOR.md` – WooCommerce and Elementor

This skill drives **OpenClaw on the host** (optional plugin tools: connection check, REST, WP-CLI, optional media upload, optional scoped plugin file I/O; otherwise `exec`/`curl`, browser, workspace)—not execution inside WordPress PHP.
