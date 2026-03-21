# ClawHub update v1.0.1 — English listing + plugin pitch

**Skill page:** [clawhub.ai/realM1lF/wordpress-site-ops](https://clawhub.ai/realM1lF/wordpress-site-ops)

## What changed

- **`SKILL.md`:** Full **English** copy (YAML `description` + body). ClawHub shows this in the teaser and preview—no more German at the top.
- **`README.md`:** English **“At a glance”** block: what the skill does, **why the companion plugin helps**, and **copy-paste integration** (clone → `npm install` → `plugins install -l` → enable → restart → env pointers).

## Publish from console (after `clawhub login`)

From monorepo root:

```bash
cd /path/to/personal-ki-agents
./scripts/package-wordpress-site-ops-for-clawhub.sh
npx --yes skills-ref validate ./build/clawhub-publish/wordpress-site-ops
```

Then (same slug as v1.0.0):

```bash
clawhub publish ./build/clawhub-publish/wordpress-site-ops \
  --slug wordpress-site-ops \
  --name "WordPress Site Ops" \
  --version 1.0.1 \
  --changelog "English SKILL.md + README for ClawHub; clearer companion plugin (wordpress-site-tools) and quick install steps. Plugin: https://github.com/realM1lF/openclaw-wordpress-tool" \
  --tags latest
```

**Requirements:** `npm i -g clawhub` (or pnpm), **`clawhub login`** once, network access.

## Web UI alternative

If you do not use the CLI: run the package script, zip the folder `build/clawhub-publish/wordpress-site-ops` (or use ClawHub **Upload** and select that folder), and set version **1.0.1** and changelog text similar to above.

## Optional: display name on ClawHub

If the page title still shows “WordPress Expert”, change it in the ClawHub project settings or pass **`--name "WordPress Site Ops"`** on publish so it matches the skill branding.
