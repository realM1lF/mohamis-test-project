# OpenClaw: Tool-Policy, Sandbox und dieses Projekt

Kurzreferenz, wie OpenClaw **Tools**, **Skills**, **Plugins** und **Sandbox** zusammenspielen – abgestimmt auf den Skill **wordpress-site-ops** und das Plugin **wordpress-site-tools**. Offizielle Quellen immer zuerst prüfen, wenn sich eure OpenClaw-Version unterscheidet.

## Offizielle Dokumentation (Einstieg)

- [Tools and Plugins](https://docs.openclaw.ai/tools) – Ueberblick Built-ins, Allow/Deny, Profile, Gruppen
- [Skills](https://docs.openclaw.ai/tools/skills)
- [Skills Config](https://docs.openclaw.ai/tools/skills-config) – `skills.entries`, `env`, Sandbox-Hinweise
- [Creating skills](https://docs.openclaw.ai/tools/creating-skills)
- [Plugins / Building Plugins (Agent Tools)](https://docs.openclaw.ai/plugins/building-plugins) – optionale Tools, `tools.allow`, Plugin-ID
- [Sandbox vs Tool Policy vs Elevated](https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated) – **Sandbox** vs **Tool-Allowlisten** vs **elevated exec**

## Globale Tool-Policy (`tools.allow` / `tools.deny`)

- Laut OpenClaw: **`tools.deny` gewinnt** immer ueber Allow.
- Zusaetzlich kann **`tools.profile`** (z. B. `full`, `coding`, `minimal`) eine **Basis-Allowlist** setzen; danach greifen globale und ggf. pro-Agent-**`allow`/`deny`**.
- Die WordPress-Plugin-Tools (`wordpress_rest_request`, … oder Bundle **`wordpress-site-tools`**) muessen in der **effektiven** Policy **erlaubt** sein – sonst erscheinen sie dem Agent nicht oder werden blockiert, **auch wenn** `tools.allow` im JSON steht, aber `deny` oder ein restriktives Profil dagegenhaelt.

Details und Schichten: [Sandbox vs Tool Policy](https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated).

## Tool-Gruppen (`group:*`)

In Allow-/Deny-Listen duerfen **Kurzschreibweisen** wie `group:fs`, `group:runtime`, `group:openclaw` stehen.

**Wichtig fuer dieses Projekt:** Laut OpenClaw-Doku umfasst **`group:openclaw`** die **eingebauten** OpenClaw-Tools – **ohne** Tools aus **externen Plugins**. Die Tools von **wordpress-site-tools** sind **nicht** automatisch in `group:openclaw`.

Daher: WordPress-Tools **explizit** eintragen, z. B.:

- einzeln: `wordpress_connection_check`, `wordpress_rest_request`, `wordpress_wp_cli`, `wordpress_media_upload`, oder
- **Bundle:** `wordpress-site-tools` (alle Tools dieses Plugins), sofern eure OpenClaw-Version das unterstuetzt (siehe [Agent Tools](https://docs.openclaw.ai/plugins/agent-tools)).

## Sandbox und Plugin-Tools

Wenn der Agent in einer **sandboxed** Session laeuft (Docker o. a.), gibt es laut OpenClaw eine **zusaetzliche** Policy:

- `tools.sandbox.tools.allow` / `tools.sandbox.tools.deny` (global oder unter `agents.list[].tools.sandbox.tools.*`)

Plugin-Tools sind **nicht** automatisch erlaubt, nur weil sie in der **globalen** `tools.allow` stehen. Bei Meldungen wie **„Tool … blocked by sandbox tool policy“** die WordPress-Tools (oder `wordpress-site-tools`) auch in **`tools.sandbox.tools.allow`** aufnehmen (konkrete Pfade: [Sandbox vs Tool Policy](https://docs.openclaw.ai/gateway/sandbox-vs-tool-policy-vs-elevated)).

**Diagnose:**

```bash
openclaw sandbox explain
openclaw sandbox explain --session agent:main:main
```

zeigt u. a. effektive Sandbox-Tool-Allowlists.

## Umgebungsvariablen: Skill-Env vs. Sandbox-Container

Laut [Skills Config](https://docs.openclaw.ai/tools/skills-config):

- `skills.entries.<skillKey>.env` gilt fuer **Host-Laeufe**; Variablen werden typischerweise nur gesetzt, wenn sie noch nicht existieren.
- In einer **Sandbox** erbt der Container **nicht** den `process.env` des Hosts.

Fuer **WORDPRESS_*** und ggf. **PATH** (damit `wp` / `curl` / `ddev` gefunden werden) in sandboxed Sessions daher z. B.:

- `agents.defaults.sandbox.docker.env`, oder
- pro Agent: `agents.list[].sandbox.docker.env`, oder
- angepasstes Sandbox-Image

Siehe auch [AUTH.md](AUTH.md) und [CONNECTING.md](CONNECTING.md).

## `tools.byProvider` (Randfall)

OpenClaw erlaubt **pro Provider/Modell** eigene Tool-Restriktionen (`tools.byProvider`). Wenn Tools trotz globaler `tools.allow` fehlen, diese Schicht prüfen (siehe [Tools](https://docs.openclaw.ai/tools)).

## WordPress-Skill / Plugin (Kurz)

| Thema | Wo |
|--------|-----|
| Anbindung, `openclaw.json`, Topologien | [CONNECTING.md](CONNECTING.md) |
| Zugangsdaten | [AUTH.md](AUTH.md) |
| DDEV / `ddev wp` | [DDEV.md](DDEV.md) |
| Plugin-Tools registrieren, optional | [openclaw-wordpress-tools/README.md](../../openclaw-wordpress-tools/README.md) |
| Nach Plugin-/Allowlist-Aenderung | **`openclaw gateway restart`**; Chat `/new` nur bei veralteter UI-Tool-Liste ([README.md](../README.md), [CONNECTING.md](CONNECTING.md)) |

Tool-Namen dieses Plugins: `wordpress_connection_check`, `wordpress_rest_request`, `wordpress_wp_cli`, `wordpress_media_upload`, `wordpress_plugin_files` (oder Bundle-ID **`wordpress-site-tools`**).

## Siehe auch

- [PLUGIN_DEV_PLAYBOOK.md](PLUGIN_DEV_PLAYBOOK.md) – Plugin-Code unter OpenClaw (ohne In-WP-Levi-Tools)
- [TOOLING.md](TOOLING.md) – wann welches Werkzeug fuer WordPress
- [NATIVE_VS_PLUGIN.md](NATIVE_VS_PLUGIN.md) – Plugin vs. `exec` / Browser / Workspace
- [CONNECTING.md](CONNECTING.md) – Anbindung, Verifikation, Fehlersuche
