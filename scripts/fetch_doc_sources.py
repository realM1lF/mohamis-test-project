#!/usr/bin/env python3
"""Fetch configured external doc sources into per-agent memory files.

Configuration:
  agents/<agent_id>/config.yaml
    doc_sources:
      - url: https://example.com/llms.txt
        target: memories/systems/Example/EXAMPLE_DOCS.txt
        enabled: true
        timeout: 30

This script is intended to run from cron (e.g. daily).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = ROOT / "agents"


@dataclass
class DocSource:
    agent_id: str
    url: str
    target: str
    enabled: bool = True
    timeout: int = 30


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_sources(agent_dir: Path) -> list[DocSource]:
    cfg_path = agent_dir / "config.yaml"
    if not cfg_path.exists():
        return []
    try:
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"[WARN] Could not parse {cfg_path}: {exc}")
        return []

    items = raw.get("doc_sources", [])
    if not isinstance(items, list):
        return []

    sources: list[DocSource] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "")).strip()
        target = str(item.get("target", "")).strip()
        if not url or not target:
            continue
        timeout_raw = item.get("timeout", 30)
        try:
            timeout = int(timeout_raw)
        except Exception:
            timeout = 30
        sources.append(
            DocSource(
                agent_id=agent_dir.name,
                url=url,
                target=target,
                enabled=bool(item.get("enabled", True)),
                timeout=max(5, timeout),
            )
        )
    return sources


def _iter_agents(agent_filter: str | None) -> list[Path]:
    if agent_filter:
        candidate = AGENTS_ROOT / agent_filter
        return [candidate] if candidate.is_dir() else []
    return sorted([p for p in AGENTS_ROOT.iterdir() if p.is_dir()])


def _fetch_text(url: str, timeout: int) -> str:
    req = urllib.request.Request(
        url=url,
        headers={"User-Agent": "personal-ki-agents-doc-fetcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        raw = resp.read()
        encoding = resp.headers.get_content_charset() or "utf-8"
    try:
        return raw.decode(encoding, errors="replace")
    except Exception:
        return raw.decode("utf-8", errors="replace")


def _safe_target_path(agent_id: str, target: str) -> Path:
    base = (AGENTS_ROOT / agent_id).resolve()
    target_path = (base / target).resolve()
    if base != target_path and base not in target_path.parents:
        raise ValueError(f"Target path escapes agent directory: {target}")
    return target_path


def _process_source(source: DocSource, dry_run: bool) -> tuple[str, str]:
    """Return (status, message). status in {updated, unchanged, skipped, failed}."""
    if not source.enabled:
        return "skipped", f"disabled: {source.url}"
    try:
        fetched = _fetch_text(source.url, source.timeout).strip()
        if not fetched:
            return "failed", f"empty response: {source.url}"
        target_path = _safe_target_path(source.agent_id, source.target)
        current = target_path.read_text(encoding="utf-8").strip() if target_path.exists() else ""

        if _sha256(fetched) == _sha256(current):
            return "unchanged", source.target

        if dry_run:
            return "updated", f"would update: {source.target}"

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(fetched + "\n", encoding="utf-8")
        return "updated", f"{source.target} <- {source.url}"
    except Exception as exc:
        return "failed", f"{source.url}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch doc_sources for agents")
    parser.add_argument("--agent", help="Only process one agent id (e.g. mohami)")
    parser.add_argument("--dry-run", action="store_true", help="No file writes")
    args = parser.parse_args()

    if not AGENTS_ROOT.exists():
        print(f"[ERROR] Missing agents directory: {AGENTS_ROOT}")
        return 2

    totals: dict[str, int] = {"total": 0, "updated": 0, "unchanged": 0, "skipped": 0, "failed": 0}
    agents = _iter_agents(args.agent)
    if not agents:
        print("[INFO] No matching agents found.")
        return 0

    for agent_dir in agents:
        sources = _load_sources(agent_dir)
        if not sources:
            continue
        print(f"\n[AGENT] {agent_dir.name} - configured sources: {len(sources)}")
        for source in sources:
            totals["total"] += 1
            status, message = _process_source(source, args.dry_run)
            totals[status] += 1
            label = status.upper()
            print(f"  [{label}] {message}")

    print(
        "\n[SUMMARY] "
        + ", ".join(f"{k}={v}" for k, v in totals.items())
    )
    return 1 if totals["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
