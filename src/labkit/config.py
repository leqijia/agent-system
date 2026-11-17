"""Locate the project root and load `lab.toml`."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = "lab.toml"

DEFAULTS: dict = {
    "paths": {
        "runs": "experiments/runs",
        "registry": "experiments/registry.jsonl",
        "ledger": "project/ledger.jsonl",
        "tasks": "project/tasks",
        "reviews": "project/reviews",
    },
    "budgets": {
        "runs_per_day": 200,
        "compute_seconds_per_day": 14400,
        "agent_calls_per_day": 40,
        "agent_usd_per_day": 10.0,
        "agent_usd_per_call": 2.0,
    },
    "check": {"command": ["uv", "run", "pytest", "-q"], "timeout_s": 600},
    "engines": {"implementer": "claude", "reviewer": "codex", "timeout_s": 900},
}


class LabError(Exception):
    """A problem the user or agent can fix; printed without a traceback."""


class BudgetError(LabError):
    """A cap was reached. Raising it is the system working, not a bug."""


@dataclass
class Config:
    root: Path
    data: dict = field(default_factory=dict)

    def path(self, key: str) -> Path:
        return self.root / self.data["paths"][key]

    def budget(self, key: str) -> float:
        return self.data["budgets"][key]


def find_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        if (folder / CONFIG_NAME).is_file():
            return folder
    raise LabError(f"no {CONFIG_NAME} found in {here} or any parent folder")


def load(start: Path | None = None) -> Config:
    root = find_root(start)
    with open(root / CONFIG_NAME, "rb") as fh:
        user = tomllib.load(fh)
    data = {section: {**values, **user.get(section, {})} for section, values in DEFAULTS.items()}
    return Config(root=root, data=data)
