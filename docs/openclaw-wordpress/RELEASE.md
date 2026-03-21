# Release-Checkliste: wordpress-site-ops

Wiederholbarer Ablauf vor **Tag**, **Release-Commit** oder **ClawHub-Version**. Detaillierte manuelle Tests: **[TEST_MATRIX.md](TEST_MATRIX.md)**.

## Vor Commit / Tag / Publish

- [ ] **TEST_MATRIX:** fuer eure Topologie relevante Zeilen (T1–T11) abgearbeitet; optional T12 wenn neue MU-Routen existieren ([TEST_MATRIX.md](TEST_MATRIX.md))
- [ ] **skills-ref:** `npx --yes skills-ref validate` gegen Verzeichnis **`wordpress-site-ops`** (nicht `openclaw-wordpress-skill`) – Details [QA.md](QA.md)
- [ ] **Keine Secrets:** keine `.env` im Commit, keine echten Passwoerter/Keys in Beispielen (nur Platzhalter)
- [ ] **MU-Plugin geaendert:** Konstante/Version in `openclaw-site-helper.php` und [README.md](../../openclaw-wordpress-skill/bundled/mu-plugin/README.md) angepasst; ggf. neue Tests in TEST_MATRIX

## Festhalten (Commit-Message, Git-Tag-Annotation oder Ticket)

Empfohlen mit abgeben:

- Datum der Pruefung
- OpenClaw-Version (CLI/Gateway, wie verfuegbar)
- WordPress-Version der Test-Site
- Topologie: **REST-only** oder **REST+WP-CLI**
- Optional: WooCommerce ja/nein
- Welche Matrix-IDs ihr ausgefuehrt habt (z. B. `T1,T3,T6,T7`)

**Beispiel** (Tag-Annotation):

```text
wordpress-site-ops x.y.z
Getestet: 2026-03-16, OpenClaw …, WP 6.x, REST+WP-CLI, Woo nein
Matrix: T1,T3,T6,T7,T10
```

## ClawHub

Publish-Flow, Slug und Bundle-Hinweise: [CLAWHUB_PUBLISH.md](CLAWHUB_PUBLISH.md).
