# Maintainer: OpenClaw WordPress Skill + Plugin

Dokumentation fuer **Release**, **Tests**, **ClawHub** und **Roadmap** – liegt **ausserhalb** des Skill-Bundles (`openclaw-wordpress-skill/`), damit ClawHub-Installs schlank bleiben.

## Erste Veroeffentlichung (Reihenfolge fuer dich)

1. **ClawHub-Account** anlegen (typisch Anmeldung mit GitHub auf [clawhub.ai](https://clawhub.ai) – genau laut aktueller OpenClaw-/ClawHub-Doku).
2. **CLI:** `npm i -g clawhub` (oder `pnpm add -g clawhub`).
3. **Skill-Ordner fuer ClawHub:** **Nicht** den Rohklon waehlen – ClawHub erlaubt nur Textdateien. Paket bauen: `./scripts/package-wordpress-site-ops-for-clawhub.sh` → Ordner **`build/clawhub-publish/wordpress-site-ops`** bei ClawHub auswaehlen (Details [CLAWHUB_PUBLISH.md](CLAWHUB_PUBLISH.md)).
4. **Validierung:** laeuft automatisch am Ende des Paket-Skripts (`Valid skill`).
5. **`clawhub login`** (einmalig).
6. **`clawhub publish …`** – exakte Zeilen: [CLAWHUB_PUBLISH.md](CLAWHUB_PUBLISH.md) (Version/Changelog anpassen).
7. **Plugin** ist **nicht** auf ClawHub: oeffentliches Repo **[github.com/realM1lF/openclaw-wordpress-tool](https://github.com/realM1lF/openclaw-wordpress-tool)** (Monorepo-Ordner weiter `openclaw-wordpress-tools/`) – Details [CLAWHUB_PUBLISH.md](CLAWHUB_PUBLISH.md).
8. **Nach erfolgreichem Publish:** ClawHub-URL des Skills schicken oder selbst in [ROADMAP_RESEARCH.md](ROADMAP_RESEARCH.md) §3 eintragen.

**Vollstaendige Details:** [CLAWHUB_PUBLISH.md](CLAWHUB_PUBLISH.md) · **Vor Release testen:** [RELEASE.md](RELEASE.md) + [TEST_MATRIX.md](TEST_MATRIX.md).

| Datei | Inhalt |
|-------|--------|
| [CLAWHUB_PUBLISH.md](CLAWHUB_PUBLISH.md) | Skill auf ClawHub veroeffentlichen; Plugin separates Git-Repo |
| [QA.md](QA.md) | Checkliste nach Installation; `skills-ref validate` |
| [TEST_MATRIX.md](TEST_MATRIX.md) | Manuelle Testfaelle Skill + Plugin |
| [RELEASE.md](RELEASE.md) | Checkliste vor Tag/Publish |
| [ROADMAP_RESEARCH.md](ROADMAP_RESEARCH.md) | Roadmap / erledigte Meta-Themen |

**Pfade im Monorepo:**

- Skill: `openclaw-wordpress-skill/`
- Plugin: `openclaw-wordpress-tools/`
- Sync: `scripts/sync-openclaw-wordpress.sh`

**Validierung vor ClawHub-Publish:**

```bash
npx --yes skills-ref validate /ABS/PFAD/zu/wordpress-site-ops
```

Details: [QA.md](QA.md).
