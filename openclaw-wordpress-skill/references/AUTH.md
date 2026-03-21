# Authentifizierung

## Prinzipien

- **Keine** Passwörter, Application Passwords oder Tokens in Chat, Git oder Skill-Dateien.
- Nutze **Umgebungsvariablen** oder OpenClaw **`skills.entries.<key>.env`** (Host-Run). In der **Sandbox** dieselben Secrets/Env ggf. unter **`agents.defaults.sandbox.docker.env`** (oder pro Agent) setzen – siehe [OPENCLAW_INTEGRATION.md](OPENCLAW_INTEGRATION.md) und [Skills config](https://docs.openclaw.ai/tools/skills-config).

**Anbindung einer bestehenden Site:** Schrittfolge und zwei Topologien (nur REST vs. REST+WP-CLI auf dem Gateway-Host) in [CONNECTING.md](CONNECTING.md). OpenClaw: [Skills](https://docs.openclaw.ai/tools/skills), [Skills config](https://docs.openclaw.ai/tools/skills-config).

## Empfohlenes Schema (REST)

| Variable | Bedeutung |
|----------|-----------|
| `WORDPRESS_SITE_URL` | Basis-URL der **Site** (ohne trailing slash), z. B. `https://staging.example.com` oder mit Unterverzeichnis `https://example.com/blog` – REST wird als `{URL}/wp-json/...` aufgeloest |
| `WORDPRESS_USER` | Benutzername für Basic Auth + Application Password |
| `WORDPRESS_APPLICATION_PASSWORD` | Von WP-Benutzerprofil generiert (nicht das Login-Passwort) |

WordPress: Benutzer → Profil → **Application Passwords** anlegen, HTTPS erzwingen.

Das OpenClaw-Plugin **`wordpress-site-tools`** nutzt fuer REST (**`wordpress_rest_request`**, **`wordpress_media_upload`**) und fuer den Auth-Teil von **`wordpress_connection_check`** dieselben drei Variablen bzw. optional `baseUrl` / `user` / `applicationPassword` in `plugins.entries.wordpress-site-tools.config` (siehe `openclaw-wordpress-tools/README.md`).

Beispiel (nur Illustration – Werte nie committen):

```bash
curl -sS -u "$WORDPRESS_USER:$WORDPRESS_APPLICATION_PASSWORD" \
  "$WORDPRESS_SITE_URL/wp-json/wp/v2/posts?per_page=1"
```

## WP-CLI

Kein Application Password nötig, wenn `wp` **auf dem Server mit Zugriff auf die Installation** läuft. Dafür typisch:

- **`WORDPRESS_PATH`**: Verzeichnis, unter dem `wp` laeuft (wird vom Plugin-Tool **`wordpress_wp_cli`** als `cwd` genutzt) oder festes `--path=` in dokumentierten Aufrufen ueber **`exec`**.
- Optional Override: `plugins.entries.wordpress-site-tools.config.wordpressPath`.
- Erweiterte WP-CLI-Befehle (ueber die Default-Allowlist hinaus): `wpCliAllowPrefixes` in derselben Plugin-Config (ersetzt die Defaults, wenn die Liste nicht leer ist). Fertige Presets: [WPCLI_PRESETS.md](WPCLI_PRESETS.md).

Siehe `.env.example` im Skill-Root.

## `.env` lokal

Datei `.env` im Skill-Verzeichnis **nicht** committen (siehe `.gitignore`). Optional: Symlink zu einem Secrets-Store außerhalb des Repos.
