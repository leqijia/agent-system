"""The experiment controller: validate, screen, run, score and record one experiment.

No language model runs in here. An agent proposes a config; this code decides what the
result was.
"""

from __future__ import annotations

import json
import math
import os
import re
import signal
import subprocess
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from labkit import registry
from labkit.config import BudgetError, Config, LabError
from labkit.identity import run_identity

LOG_TAIL_LINES = 15


@dataclass
class Spec:
    id: str
    command: list[str]
    path: Path
    config: dict = field(default_factory=dict)
    seed: int = 0
    timeout_s: float = 600
    code: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    evaluate: list[str] | None = None
    primary_metric: str | None = None
    direction: str = "min"
    max_runs: int = 50
    bounds: dict = field(default_factory=dict)
    screen: dict | None = None


def load_spec(path: Path) -> Spec:
    if not path.is_file():
        raise LabError(f"spec not found: {path}")
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    for key in ("id", "command"):
        if key not in raw:
            raise LabError(f"{path}: missing required key '{key}'")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", raw["id"]):
        raise LabError(f"{path}: id may only contain letters, digits, '_', '.', '-'")
    unknown = set(raw) - (set(Spec.__dataclass_fields__) - {"path"})
    if unknown:
        raise LabError(f"{path}: unknown keys {sorted(unknown)}")
    spec = Spec(path=path, **raw)
    if spec.direction not in ("min", "max"):
        raise LabError(f"{path}: direction must be 'min' or 'max'")
    return spec


def apply_overrides(spec: Spec, sets: list[str], seed: int | None = None) -> None:
    """Apply `key=value` overrides. Unknown keys are rejected so typos cannot slip through."""
    for item in sets:
        key, sep, text = item.partition("=")
        if not sep:
            raise LabError(f"override must look like key=value, got: {item}")
        if key not in spec.config:
            raise LabError(f"'{key}' is not in [config] of {spec.path.name}: {sorted(spec.config)}")
        try:
            spec.config[key] = json.loads(text)
        except json.JSONDecodeError:
            spec.config[key] = text
    if seed is not None:
        spec.seed = seed


def _outside(value: object, limits: list) -> bool:
    low, high = limits
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return True
    return not (low <= value <= high)


def validate(spec: Spec) -> list[str]:
    """Cheap checks that run before any compute is spent."""
    problems = []
    for key, limits in spec.bounds.items():
        if key not in spec.config:
            problems.append(f"[bounds] names '{key}', which is not in [config]")
        elif _outside(spec.config[key], limits):
            problems.append(f"{key}={spec.config[key]!r} is outside allowed range {limits}")
    return problems


def check_budgets(cfg: Config, spec: Spec, records: list[dict]) -> None:
    used = sum(1 for r in records if r["spec"] == spec.id and r["stage"] == "full")
    if used >= spec.max_runs:
        raise BudgetError(
            f"spec '{spec.id}' has used {used} of max_runs={spec.max_runs}. "
            "Stop and report; raising the cap is a human decision."
        )
    today = registry.from_today(records)
    if len(today) >= cfg.budget("runs_per_day"):
        raise BudgetError(f"daily run cap reached ({len(today)} runs today)")
    seconds = sum(r.get("seconds", 0) for r in today)
    if seconds >= cfg.budget("compute_seconds_per_day"):
        raise BudgetError(f"daily compute cap reached ({seconds:.0f}s used today)")


def read_metrics(path: Path) -> tuple[dict, str | None]:
    if not path.is_file():
        return {}, "the run exited 0 but wrote no metrics.json into $LAB_RUN_DIR"
    try:
        metrics = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return {}, f"metrics.json is not valid JSON: {exc}"
    if not isinstance(metrics, dict) or not metrics:
        return {}, "metrics.json must be a non-empty JSON object"
    for name, value in metrics.items():
        number = isinstance(value, (int, float)) and not isinstance(value, bool)
        if not number or not math.isfinite(value):
            return {}, f"metric '{name}' is not a finite number: {value!r}"
    return metrics, None


def _git_state(root: Path) -> tuple[str | None, bool]:
    def git(*args: str) -> str | None:
        try:
            out = subprocess.run(
                ["git", *args], cwd=root, capture_output=True, text=True, timeout=20
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return out.stdout.strip() if out.returncode == 0 else None

    return git("rev-parse", "--short", "HEAD"), bool(git("status", "--porcelain"))


def _run_command(command: list[str], *, cwd: Path, env: dict, log, timeout: float) -> str:
    try:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # lets a timeout kill the whole process tree
        )
    except OSError as exc:
        raise LabError(f"cannot start {command[0]!r}: {exc}") from exc
    try:
        return "ok" if proc.wait(timeout=timeout) == 0 else "failed"
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        return "timeout"


def _execute(
    cfg: Config, spec: Spec, run_id: str, payload: dict, *, stage: str, timeout: float
) -> dict:
    run_dir = cfg.path("runs") / spec.id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    config_path = run_dir / "config.json"
    config_path.write_text(json.dumps({"config": payload["config"], "seed": spec.seed}, indent=2))
    (run_dir / "identity.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    metrics_path = run_dir / "metrics.json"
    metrics_path.unlink(missing_ok=True)
    env = {
        **os.environ,
        "LAB_RUN_DIR": str(run_dir),
        "LAB_CONFIG": str(config_path),
        "LAB_SEED": str(spec.seed),
    }

    started = time.monotonic()
    note = None
    with open(run_dir / "log.txt", "w", encoding="utf-8") as log:
        status = _run_command(spec.command, cwd=cfg.root, env=env, log=log, timeout=timeout)
        if status == "ok" and spec.evaluate:
            log.write("\n--- evaluate ---\n")
            log.flush()
            status = _run_command(spec.evaluate, cwd=cfg.root, env=env, log=log, timeout=timeout)
            if status != "ok":
                note = f"evaluate command {status}"
    seconds = round(time.monotonic() - started, 2)

    metrics: dict = {}
    if status == "ok":
        metrics, note = read_metrics(metrics_path)
        if note:
            status = "no_metrics"

    commit, dirty = _git_state(cfg.root)
    record = {
        "time": registry.now(),
        "run_id": run_id,
        "spec": spec.id,
        "stage": stage,
        "status": status,
        "metrics": metrics,
        "config": payload["config"],
        "seed": spec.seed,
        "seconds": seconds,
        "git_commit": commit,
        "git_dirty": dirty,
        "run_dir": run_dir.relative_to(cfg.root).as_posix(),
    }
    if note:
        record["note"] = note
    registry.append(cfg.path("registry"), record)
    return record


def _cached(records: list[dict], run_id: str) -> dict | None:
    """Only successful runs are reused; a failed run may be retried and can resume."""
    for record in reversed(records):
        if record["run_id"] == run_id and record["status"] == "ok":
            return record
    return None


def _run_stage(cfg: Config, spec: Spec, records: list[dict], *, stage: str) -> dict:
    config = dict(spec.config)
    timeout = spec.timeout_s
    if stage == "screen":
        config.update(spec.screen.get("overrides", {}))
        timeout = spec.screen.get("timeout_s", spec.timeout_s)
    run_id, payload = run_identity(
        cfg.root,
        command=spec.command + (spec.evaluate or []),
        config=config,
        seed=spec.seed,
        code=spec.code,
        inputs=spec.inputs,
        stage=stage,
    )
    hit = _cached(records, run_id)
    if hit:
        return {**hit, "cached": True}
    return _execute(cfg, spec, run_id, payload, stage=stage, timeout=timeout)


def _screen_problem(spec: Spec, record: dict) -> str | None:
    if record["status"] != "ok":
        return f"screening run {record['run_id']} ended with status {record['status']}"
    for name, limits in spec.screen.get("bounds", {}).items():
        value = record["metrics"].get(name)
        if _outside(value, limits):
            return f"screening metric {name}={value!r} is outside {limits}"
    return None


def run_spec(cfg: Config, spec: Spec) -> dict:
    """Run one experiment end to end and return its registry record."""
    problems = validate(spec)
    if problems:
        raise LabError("invalid config, nothing was run:\n  " + "\n  ".join(problems))
    records = registry.read(cfg.path("registry"))

    full_id, _ = run_identity(
        cfg.root,
        command=spec.command + (spec.evaluate or []),
        config=spec.config,
        seed=spec.seed,
        code=spec.code,
        inputs=spec.inputs,
    )
    hit = _cached(records, full_id)
    if hit:
        return {**hit, "cached": True}

    check_budgets(cfg, spec, records)
    if spec.screen:
        screened = _run_stage(cfg, spec, records, stage="screen")
        problem = _screen_problem(spec, screened)
        if problem:
            record = {
                "time": registry.now(),
                "run_id": full_id,
                "spec": spec.id,
                "stage": "full",
                "status": "screened_out",
                "metrics": {},
                "config": spec.config,
                "seed": spec.seed,
                "seconds": 0,
                "run_dir": screened["run_dir"],
                "note": problem,
            }
            registry.append(cfg.path("registry"), record)
            return record
    return _run_stage(cfg, spec, records, stage="full")


def best_run(records: list[dict], spec_id: str, metric: str | None, direction: str) -> dict | None:
    scored = [
        r
        for r in records
        if r["spec"] == spec_id
        and r["stage"] == "full"
        and r["status"] == "ok"
        and metric in r["metrics"]
    ]
    if not scored:
        return None
    pick = min if direction == "min" else max
    return pick(scored, key=lambda r: r["metrics"][metric])


def log_tail(cfg: Config, record: dict, lines: int = LOG_TAIL_LINES) -> str:
    log = cfg.root / record["run_dir"] / "log.txt"
    if not log.is_file():
        return ""
    return "\n".join(log.read_text(errors="replace").splitlines()[-lines:])


def summarize(cfg: Config, spec: Spec, record: dict) -> str:
    """A compact result meant to be read by an agent: outcome first, paths for the detail."""
    cached = "  (cached, nothing was re-run)" if record.get("cached") else ""
    out = [
        f"run {record['run_id']}  spec={record['spec']}  status={record['status']}"
        f"  {record['seconds']}s{cached}"
    ]
    for name, value in sorted(record["metrics"].items()):
        out.append(f"  {name} = {value:.6g}")
    if record.get("note"):
        out.append(f"  note: {record['note']}")
    if record["status"] in ("failed", "timeout", "no_metrics"):
        out.append(f"  last log lines:\n{_indent(log_tail(cfg, record))}")
    records = registry.read(cfg.path("registry"))
    best = best_run(records, spec.id, spec.primary_metric, spec.direction)
    if best:
        marker = "this run" if best["run_id"] == record["run_id"] else f"run {best['run_id']}"
        value = best["metrics"][spec.primary_metric]
        out.append(f"  best {spec.primary_metric} so far: {value:.6g} ({marker})")
    used = sum(1 for r in records if r["spec"] == spec.id and r["stage"] == "full")
    out.append(f"  runs used: {used}/{spec.max_runs}   artifacts: {record['run_dir']}/")
    return "\n".join(out)


def _indent(text: str) -> str:
    return "\n".join("    " + line for line in text.splitlines())
