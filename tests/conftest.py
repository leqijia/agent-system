"""Shared fixtures: a throwaway project with a tiny runner, so tests never touch real data."""

import sys
import textwrap

import pytest

from labkit import config

RUNNER = """
import json, os, subprocess, sys, time
from pathlib import Path

settings = json.loads(Path(os.environ["LAB_CONFIG"]).read_text())
cfg = settings["config"]
with open("calls.log", "a") as fh:
    fh.write(json.dumps(cfg) + "\\n")
if cfg.get("spawn"):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    Path("child.pid").write_text(str(child.pid))
if cfg.get("sleep"):
    time.sleep(cfg["sleep"])
if cfg.get("fail"):
    print("boom: deliberate failure")
    sys.exit(1)
if not cfg.get("silent"):
    out = Path(os.environ["LAB_RUN_DIR"]) / "metrics.json"
    out.write_text(json.dumps({"loss": cfg["x"] ** 2}))
"""

SPEC = """
id = "toy"
command = ["{python}", "runner.py"]
code = ["runner.py"]
timeout_s = 20
primary_metric = "loss"
max_runs = 5

[config]
x = 3
sleep = 0
fail = false
silent = false
spawn = false

[bounds]
x = [-10, 10]
"""


@pytest.fixture
def project(tmp_path):
    (tmp_path / "lab.toml").write_text("[budgets]\nruns_per_day = 100\n")
    (tmp_path / "runner.py").write_text(textwrap.dedent(RUNNER))
    (tmp_path / "toy.toml").write_text(SPEC.format(python=sys.executable))
    return config.load(tmp_path)


@pytest.fixture
def calls(project):
    """How many times the runner was really started."""

    def count() -> int:
        log = project.root / "calls.log"
        return len(log.read_text().splitlines()) if log.is_file() else 0

    return count
