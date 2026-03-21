# Vorbereitung: Tiefenarbeit

Abgeschlossenes und offenes – fuer laengere Iterationen ausserhalb kleiner Textaenderungen.

Fortschritt u. a. in [PLUGIN_DEV_PLAYBOOK.md](../../openclaw-wordpress-skill/references/PLUGIN_DEV_PLAYBOOK.md), [TEST_MATRIX.md](TEST_MATRIX.md), [CONNECTING.md](../../openclaw-wordpress-skill/references/CONNECTING.md) (Betriebsprofile).

## 1. Eigene OpenClaw-Tools (Plugin)

- [x] OpenClaw [Building Plugins](https://docs.openclaw.ai/plugins/building-plugins) / Plugin-SDK: `registerTool`, TypeBox, optionale Tools (`openclaw-wordpress-tools/` im Repo).
- [x] Minimales Tool **`wordpress_rest_request`** (method, path, query, body); Base-URL/Auth aus Env (`WORDPRESS_*`) oder `plugins.entries.wordpress-site-tools.config`.
- [x] **`wordpress_wp_cli`** mit Allowlist-Praefixen, globaler Blocklist, `spawn` ohne Shell (`openclaw-wordpress-tools/src/wp-cli.ts`).
- [x] **`wpCliProfile`** / Presets (`openclaw-wordpress-tools/src/wp-cli-presets.ts`).
- [x] **`wordpress_connection_check`** (REST + optional WP-CLI `core version`).
- [x] **`wordpress_media_upload`** (multipart `wp/v2/media`, Pfad unter `process.cwd()`).
- [x] **DDEV / lokaler WP-CLI:** `wpCliRunner` + `WORDPRESS_WP_CLI_RUNNER`, `ddev wp` im Projektroot ([DDEV.md](../../openclaw-wordpress-skill/references/DDEV.md)).
- [x] Skill-`SKILL.md` und [TOOLING.md](../../openclaw-wordpress-skill/references/TOOLING.md) auf **Tool-Namen** ausgerichtet.
- [x] OpenClaw-Policy-Doku ergänzt: [OPENCLAW_INTEGRATION.md](../../openclaw-wordpress-skill/references/OPENCLAW_INTEGRATION.md) (Tool-/Sandbox-Schichten, offizielle Links).

## 2. Gating und Metadata

- [x] `metadata.openclaw.requires`: **konservativ** `anyBins: ["wp","curl"]` beibehalten (Abgleich mit Fallbacks in [TOOLING.md](../../openclaw-wordpress-skill/references/TOOLING.md); README „Gating“). Verschmaelern nur bei bewusstem Verzicht auf Shell-Fallback-Eligibility.
- [x] `skills.entries` und Plugin/Allowlist in `openclaw.json` im [README](../../openclaw-wordpress-skill/README.md) dokumentiert.

## 3. ClawHub / AgentSkills-Validierung

- [x] [skills-ref validate](https://github.com/agentskills/agentskills/tree/main/skills-ref) gegen Ordner **`wordpress-site-ops`** (installiert z. B. `~/.openclaw/workspace/skills/wordpress-site-ops` nach [sync-Skript](../../scripts/sync-openclaw-wordpress.sh)) – **nicht** gegen `openclaw-wordpress-skill`. Befehl und lokale Kopie: [QA.md](QA.md).
- [x] [ClawHub](https://docs.openclaw.ai/tools/clawhub): Publish-Flow, Slug `wordpress-site-ops`, Secrets-Checkliste; Upload nur **Textdateien** (kein `.gitignore`, `.env.example`, kein `openclaw-site-helper.php` im Bundle) – Paket-Skript [package-wordpress-site-ops-for-clawhub.sh](../../scripts/package-wordpress-site-ops-for-clawhub.sh), [CLAWHUB_PUBLISH.md](CLAWHUB_PUBLISH.md), Skill-README Maintainer.
- [x] Nach **erstem** echten Publish: Listing **[wordpress-site-ops auf ClawHub](https://clawhub.ai/realM1lF/wordpress-site-ops)**; v1.0.1: englisches SKILL/README + Plugin-Integration siehe [CLAWHUB_RELEASE_1.0.1.md](CLAWHUB_RELEASE_1.0.1.md).

## 4. Optionales WordPress MU-Plugin (neutral)

**Stand:** **MU-Helfer** im Skill unter **[bundled/mu-plugin/](../../openclaw-wordpress-skill/bundled/mu-plugin/)** (`openclaw-site-helper.php` v0.2.0+): Routen `openclaw-helper/v1/status`, `/health` (`manage_options`), `/me/capabilities` (eingeloggt). Deploy nach `wp-content/mu-plugins/`. Agent-Doku: [MU_HELPER.md](../../openclaw-wordpress-skill/references/MU_HELPER.md).

- [x] Basis-MU-Helfer im Repo (bundled).
- [x] Zusaetzliche lesende Endpoints (Health, Capabilities) und Skill-Doku „wann sinnvoll“.

## 5. Testmatrix

- [x] Feste Liste: [TEST_MATRIX.md](TEST_MATRIX.md) (Lesen, Schreiben, 401/404, Woo-Lese-Call, WP-CLI, Sandbox-Hinweis).
- [x] Release-Prozess: [RELEASE.md](RELEASE.md) (Matrix abhaken, Umgebung/Versionen in Commit-, Tag-Text oder Ticket); Verweis auch in [QA.md](QA.md).

## 6. Zielbild: umfassender Betrieb + Plugin-Entwicklung

Nutzererwartung: WordPress **weitgehend vollstaendig** bedienbar *und* Agent als **Entwickler** (eigene Plugins, Erweiterungen fremder Plugins ueber Hooks). Siehe [USER_EXPECTATIONS.md](../../openclaw-wordpress-skill/references/USER_EXPECTATIONS.md) Abschnitt 2.1.

- [x] **WP-CLI-Presets** dokumentiert in [WPCLI_PRESETS.md](../../openclaw-wordpress-skill/references/WPCLI_PRESETS.md) (read, extended-read, content-staging, staging-admin, dev-local); Anbindungsleitfaden [CONNECTING.md](../../openclaw-wordpress-skill/references/CONNECTING.md). [x] **Runtime-Profil** im Plugin: Config `wpCliProfile` + `src/wp-cli-presets.ts` (wenn `wpCliAllowPrefixes` leer).
- [x] **NATIVE_VS_PLUGIN.md** – Abgrenzung Plugin vs. `exec` / Browser / Workspace.
- [x] **Skill-Referenzen:** [PLUGIN_DEV_PLAYBOOK.md](../../openclaw-wordpress-skill/references/PLUGIN_DEV_PLAYBOOK.md) (Hooks, REST, Sicherheit, Addon statt Fork, Links). Woo/Elementor: [WOO_ELEMENTOR.md](../../openclaw-wordpress-skill/references/WOO_ELEMENTOR.md). Optional spaeter: eigene `references/THIRD_PARTY_HOOKS.md` (ACF, …).
- [x] **Tool `wordpress_plugin_files`:** list/read/write unter `wp-content/plugins/<slug>/` (Pfad-Allowlist, Limits) in `openclaw-wordpress-tools`.
- [x] **Qualitaet:** PHPCS/WPCS, `wp i18n`, PHPUnit – dokumentiert im Playbook (kein CI im Skill).
- [x] **Sicherheit / Profile:** [SAFETY.md](../../openclaw-wordpress-skill/references/SAFETY.md) (Umgebung) + [CONNECTING.md](../../openclaw-wordpress-skill/references/CONNECTING.md) §6 Betriebsprofile; [SKILL.md](../../openclaw-wordpress-skill/SKILL.md) Regel Plugin-Entwicklung.
