"""Append-only JSON Lines logs: the experiment registry and the agent ledger."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def today() -> str:
    return now()[:10]


def append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def from_today(records: list[dict]) -> list[dict]:
    day = today()
    return [r for r in records if str(r.get("time", "")).startswith(day)]
