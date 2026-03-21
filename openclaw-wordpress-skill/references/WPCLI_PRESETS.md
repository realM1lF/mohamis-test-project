# WP-CLI-Allowlist-Presets (`wpCliProfile` / `wpCliAllowPrefixes`)

Das OpenClaw-Tool **`wordpress_wp_cli`** erlaubt nur Kommandos, deren **Token-Praefix** in einer Liste steht. Die Liste kommt in dieser **Reihenfolge**:

1. **`wpCliAllowPrefixes`** (Plugin-Config): wenn **mindestens ein** Eintrag → **ersetzt** alles andere (Defaults und Profil).
2. Sonst **`wpCliProfile`**: benannter Preset-Name → eingebaute Liste im Plugin (`openclaw-wordpress-tools/src/wp-cli-presets.ts`, synchron zu dieser Datei).
3. Sonst **builtin-default** (wie unten `builtin-default`).

**Wichtig:** Bei manueller `wpCliAllowPrefixes`-Liste muss alles, was erlaubt sein soll (inkl. `core version`), in der Liste stehen.

Jeder String ist ein Praefix aus **Tokens nach `wp`**, getrennt durch Leerzeichen, z. B. `"post list"` erlaubt `wp post list …`.

Globale **Blocklist** (immer verboten, auch in Custom-Listen): u. a. `eval`, `eval-file`, `shell`, `cli`; bei `db` u. a. `query`, `reset`, `clean`, `import`, `export`. Siehe Plugin-README.

---

## Preset: `builtin-default` (ohne Config)

Wenn ihr **keine** `wpCliAllowPrefixes` setzt und **kein** `wpCliProfile`, gelten automatisch (aequivalent zu folgenden Praefixen). Optional explizit:

```json5
wpCliProfile: "builtin-default",
```

- `core version`
- `core is-installed`
- `post list`
- `post get`
- `plugin list`
- `theme list`
- `option get`
- `user list`

**Risiko:** niedrig (ueberwiegend lesend).

---

## Preset: `extended-read`

Explizite Liste, falls ihr Defaults nachbauen und um **lesende** Befehle erweitern wollt.

**Kurz (Profil statt langer Liste):**

```json5
wpCliProfile: "extended-read",
```

**Oder** manuell als `wpCliAllowPrefixes`:

```json5
wpCliAllowPrefixes: [
  "core version",
  "core is-installed",
  "core verify-checksums",
  "post list",
  "post get",
  "page list",
  "page get",
  "plugin list",
  "theme list",
  "option get",
  "user list",
  "rewrite list",
  "db tables",
  "db check",
  "db size",
],
```

**Hinweis:** `db tables` / `db check` / `db size` sind erlaubt, solange der zweite Token **nicht** auf der Blocklist steht.

---

## Preset: `content-staging`

Fuer **Staging**: Beitraege anlegen/aendern. **Nicht** blind auf Produktion anwenden.

**Kurz:**

```json5
wpCliProfile: "content-staging",
```

**Oder** manuell:

```json5
wpCliAllowPrefixes: [
  // zuerst alles aus extended-read, falls gewuenscht – hier gekuerzt:
  "core version",
  "post list",
  "post get",
  "post create",
  "post update",
  "post delete",
  "page list",
  "page get",
  "page create",
  "page update",
  "media list",
  "media get",
  "media import",
],
```

**Risiko:** mittel bis hoch (`post delete`, `media import`). Backup und explizite Nutzerfreigabe im Chat laut [SAFETY.md](SAFETY.md).

---

## Preset: `staging-admin`

Plugin-/Theme-Lebenszyklus auf **Staging** (Aktivierung, Installation aus wordpress.org).

**Kurz:**

```json5
wpCliProfile: "staging-admin",
```

**Oder** manuell:

```json5
wpCliAllowPrefixes: [
  "core version",
  "plugin list",
  "plugin status",
  "plugin activate",
  "plugin deactivate",
  "plugin install",
  "plugin update",
  "theme list",
  "theme activate",
  "theme install",
  "theme update",
  "cache flush",
  "rewrite flush",
  "option get",
],
```

**Risiko:** hoch – aendert laufende Site und kann Updates ziehen. Nicht zusammen mit Produktions-URLs in derselben OpenClaw-Config ohne Review.

---

## Preset: `dev-local`

Nur fuer **lokale** Entwicklungsumgebungen (Scaffold, i18n). **`eval` / `eval-file` sind im Plugin immer blockiert** und duerfen nicht in Allowlists.

**Kurz:**

```json5
wpCliProfile: "dev-local",
```

**Oder** manuell:

```json5
wpCliAllowPrefixes: [
  "core version",
  "scaffold plugin",
  "scaffold post-type",
  "scaffold taxonomy",
  "i18n make-pot",
  "i18n make-json",
],
```

Optional nur bei Bedarf: `package install` (WP-CLI-Pakete; eigenes Risiko). Liste sonst minimal halten und gezielt erweitern.

---

## Einbindung in `openclaw.json` (Ausschnitt)

```json5
plugins: {
  entries: {
    "wordpress-site-tools": {
      enabled: true,
      config: {
        wordpressPath: "/pfad/zur/wp-installation",
        wpCliProfile: "content-staging",
        // Power-User (ersetzt Profil, wenn nicht leer):
        // wpCliAllowPrefixes: [ "core version", "post list", ... ],
      },
    },
  },
},
```

`wordpressPath` kann `WORDPRESS_PATH` aus der Umgebung ueberschreiben (siehe Plugin-README).

---

## Abgleich mit OpenClaw

- Plugin-Config folgt dem Schema in [openclaw.plugin.json](../../openclaw-wordpress-tools/openclaw.plugin.json) (`configSchema`).
- Aenderungen an `openclaw.json` (Allowlists, Plugin-Config): **`openclaw gateway restart`** – siehe [CONNECTING.md](CONNECTING.md) / [README.md](../README.md) (Gateway vs. Chat; `/new` ersetzt den Restart nicht).

Siehe auch [CONNECTING.md](CONNECTING.md).
