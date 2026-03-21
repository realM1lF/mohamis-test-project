# WordPress Site Ops – Referenz-Index

Kurze Uebersicht der Dateien in `references/` (Progressive Disclosure – Details nur bei Bedarf laden).

| Datei | Inhalt |
|-------|--------|
| [CONNECTING.md](CONNECTING.md) | Bestehende Site an OpenClaw: Topologien, App-Password, openclaw.json, MU-Bundle, `wordpress_plugin_files`, Verifikation, **Gateway restart vs. `/new`** |
| [../bundled/mu-plugin/README.md](../bundled/mu-plugin/README.md) | Optionaler MU-Helfer (PHP) – auf `wp-content/mu-plugins/` kopieren; Routen-Referenz |
| [MU_HELPER.md](MU_HELPER.md) | **Wann** MU-Helfer sinnvoll ist (REST-only, Sandbox, vs. WP-CLI / `wordpress_plugin_files`) |
| [OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md) | OpenClaw: globale Tool-Policy, Sandbox-Allowlists, `group:openclaw` vs. Plugin-Tools, Env Host vs. Container, offizielle Doku-Links |
| [DDEV.md](DDEV.md) | Lokale DDEV-Sites: REST-URL, `wpCliRunner` / `ddev wp`, WORDPRESS_PATH |
| [NATIVE_VS_PLUGIN.md](NATIVE_VS_PLUGIN.md) | Wann Plugin-Tools vs. OpenClaw-`exec` / Browser / Workspace |
| [WPCLI_PRESETS.md](WPCLI_PRESETS.md) | `wpCliProfile`-Presets und manuelle `wpCliAllowPrefixes` fuer das Plugin |
| [USER_EXPECTATIONS.md](USER_EXPECTATIONS.md) | Nutzererwartungen, Bedienung, Zielbild – Abgleich mit Entwicklungsstand |
| [FOR_SITE_OWNERS.md](FOR_SITE_OWNERS.md) | Einfache Sprache fuer Nutzer ohne Technik-Hintergrund |
| [TOOLING.md](TOOLING.md) | WP-CLI vs REST vs Browser; Verweis auf NATIVE_VS_PLUGIN |
| [AUTH.md](AUTH.md) | URLs, Application Passwords, Umgebungsvariablen |
| [WORKFLOWS.md](WORKFLOWS.md) | Read → Plan → Write → Verify |
| [SAFETY.md](SAFETY.md) | Draft-Defaults, riskante Optionen, destruktive Aktionen |
| [DOMAIN.md](DOMAIN.md) | Blocks, Plugins, CPT, REST, haeufige Fallstricke |
| [PLUGIN_DEV_PLAYBOOK.md](PLUGIN_DEV_PLAYBOOK.md) | Plugin-Entwicklung: Hooks, REST, Sicherheit, Qualitaet, OpenClaw-Workflow |
| [WOO_ELEMENTOR.md](WOO_ELEMENTOR.md) | WooCommerce und Elementor – Grenzen und Workflows |

Inhalt: kuratierte WordPress-/OpenClaw-Arbeitsregeln fuer Agenten auf dem Host.

**Maintainer** (ClawHub, Testmatrix, Roadmap, Release): liegen im Monorepo unter `docs/openclaw-wordpress/` – nicht im Skill-Bundle.
