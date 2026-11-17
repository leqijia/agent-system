"""`lab status`: where the project stands, in a few lines an agent or a person can act on."""

from __future__ import annotations

import subprocess

from labkit import agents, registry, tasks
from labkit.config import Config


def _git(cfg: Config, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=cfg.root, capture_output=True, text=True, timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def report(cfg: Config) -> str:
    lines = []

    branch = _git(cfg, "branch", "--show-current") or "(no branch)"
    changed = len(_git(cfg, "status", "--porcelain").splitlines())
    remote = "yes" if _git(cfg, "remote") else "none (local only)"
    lines.append(f"git: branch {branch}, {changed} uncommitted file(s), remote: {remote}")

    open_tasks = [t for t in tasks.all_tasks(cfg) if t["status"] not in ("done", "dropped")]
    lines.append(f"open tasks: {len(open_tasks)}")
    for task in open_tasks[:10]:
        lines.append(f"  {task['id']} [{task['status']}] {task['title']}")

    runs = registry.read(cfg.path("registry"))
    lines.append(f"experiment runs recorded: {len(runs)}")
    for run in runs[-3:]:
        metrics = ", ".join(f"{k}={v:.4g}" for k, v in sorted(run["metrics"].items()))
        lines.append(f"  {run['run_id']} {run['spec']} {run['status']} {metrics}".rstrip())

    runs_today = registry.from_today(runs)
    calls_today = registry.from_today(registry.read(cfg.path("ledger")))
    seconds = sum(r.get("seconds", 0) for r in runs_today)
    spent = sum(r.get("cost_usd") or 0 for r in calls_today)
    lines.append(
        "budget today: "
        f"{len(runs_today)}/{cfg.budget('runs_per_day')} runs, "
        f"{seconds:.0f}/{cfg.budget('compute_seconds_per_day')}s compute, "
        f"{len(calls_today)}/{cfg.budget('agent_calls_per_day')} agent calls, "
        f"${spent:.2f}/${cfg.budget('agent_usd_per_day'):.2f} measured agent spend"
    )

    found = agents.available()
    engines = ", ".join(f"{name}={'ok' if path else 'missing'}" for name, path in found.items())
    lines.append(f"engines: {engines}")
    return "\n".join(lines)
