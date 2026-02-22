# Externe LLM-Dokuquellen (Daily Cron)

Dieses Projekt unterstützt externe Dokuquellen pro Agent über `doc_sources` in
`agents/<agent_id>/config.yaml`.

## 1) Konfiguration pro Agent

Beispiel:

```yaml
doc_sources:
  - url: https://developer.shopware.com/llms.txt
    target: memories/systems/Shopware 6/SHOPWARE_OFFICIAL_LLM_DOCS.txt
    enabled: true
    timeout: 30

  - url: https://developer.shopware.com/llms-full.txt
    target: memories/systems/Shopware 6/SHOPWARE_OFFICIAL_LLM_DOCS_FULL.txt
    enabled: true
    timeout: 60

  - url: https://shopify.dev/llms.txt
    target: memories/systems/Shopify/SHOPIFY_OFFICIAL_LLM_DOCS.txt
    enabled: true
    timeout: 30
```

`target` ist relativ zu `agents/<agent_id>/`.

## 2) Manuell ausführen

Alle Agents:

```bash
python scripts/fetch_doc_sources.py
```

Nur ein Agent:

```bash
python scripts/fetch_doc_sources.py --agent mohami
```

Dry-Run (nur prüfen, nichts schreiben):

```bash
python scripts/fetch_doc_sources.py --agent mohami --dry-run
```

## 3) Daily Cron (1x pro Tag)

Crontab öffnen:

```bash
crontab -e
```

Beispiel-Eintrag (jeden Tag 03:00 Uhr):

```cron
0 3 * * * cd /home/rin/Work/personal-ki-agents && /usr/bin/python3 scripts/fetch_doc_sources.py >> logs/fetch_doc_sources.log 2>&1
```

## 4) Wirkung auf Memory-DB

- Der Fetcher aktualisiert Dateien unter `agents/<agent_id>/memories/...`.
- Beim nächsten Agent-Start werden diese Dateien durch den Startup-Sync in die
  Memory-DB indexiert (inkl. Hash-basierter Änderungserkennung).

