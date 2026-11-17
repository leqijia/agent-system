"""One interface over two coding agents: Claude Code (`claude -p`) and Codex (`codex exec`).

Both are called headlessly for a single bounded job. Read-only is the default; `write=True`
lets the agent edit files inside the project and nothing else.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from labkit import registry
from labkit.config import BudgetError, Config, LabError

ENGINES = ("claude", "codex")

# `--tools` decides which tools exist in the session at all. `--allowedTools` only adds to
# the project's own allow rules, so by itself it cannot make a session read-only.
CLAUDE_READ_TOOLS = "Read,Grep,Glob"
CLAUDE_WRITE_TOOLS = "Read,Grep,Glob,Edit,Write,Bash"
CLAUDE_WRITE_ALLOW = (
    "Read,Grep,Glob,Edit,Write,"
    "Bash(uv run pytest *),Bash(uv run ruff *),"
    # Not all of `lab`: `lab ask` and `lab review` would start further paid agent calls.
    "Bash(uv run lab run *),Bash(uv run lab runs *),Bash(uv run lab status),"
    "Bash(uv run lab task *),"
    "Bash(git status *),Bash(git diff *),Bash(git log *),Bash(git add *),Bash(git commit *)"
)


@dataclass
class AgentResult:
    engine: str
    ok: bool
    text: str
    seconds: float
    cost_usd: float | None = None


def available() -> dict[str, str | None]:
    return {engine: shutil.which(engine) for engine in ENGINES}


def candidates(preferred: str, *, avoid: str | None = None) -> list[str]:
    """Installed engines in the order to try them: preferred first, `avoid` last."""
    paths = available()
    found = [engine for engine in ENGINES if paths[engine]]
    if not found:
        raise LabError("neither `claude` nor `codex` is installed and on PATH")
    return sorted(found, key=lambda engine: (engine == avoid, engine != preferred))


def _failure_reason(stdout: str, stderr: str) -> str:
    """The most useful line of a failed run, without pages of startup logging."""
    lines = (stdout + "\n" + stderr).strip().splitlines()
    errors = [line for line in lines if "error" in line.lower() and "mcp" not in line.lower()]
    return (errors or lines or ["no output"])[-1].strip()[:500]


def build_argv(
    engine: str, *, write: bool, cwd: Path, max_usd: float, out_file: Path, model: str | None
) -> list[str]:
    if engine == "claude":
        argv = [
            "claude",
            "-p",
            "--output-format",
            "json",
            "--permission-mode",
            "acceptEdits" if write else "dontAsk",
            "--tools",
            CLAUDE_WRITE_TOOLS if write else CLAUDE_READ_TOOLS,
            "--allowedTools",
            CLAUDE_WRITE_ALLOW if write else CLAUDE_READ_TOOLS,
            "--strict-mcp-config",  # no MCP servers: nothing outside the repository
            "--max-budget-usd",
            str(max_usd),
        ]
        return argv + (["--model", model] if model else [])
    if engine == "codex":
        argv = [
            "codex",
            "exec",
            "--sandbox",
            "workspace-write" if write else "read-only",
            "--cd",
            str(cwd),
            "--color",
            "never",
            "--output-last-message",
            str(out_file),
        ]
        return argv + (["--model", model] if model else []) + ["-"]
    raise LabError(f"unknown engine '{engine}'; choose from {ENGINES}")


def _execute(argv: list[str], prompt: str, cwd: Path, timeout: float) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            argv, input=prompt, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout:.0f}s"
    except OSError as exc:
        raise LabError(f"cannot start {argv[0]!r}: {exc}") from exc
    return proc.returncode, proc.stdout, proc.stderr


def _parse_claude(stdout: str) -> tuple[bool, str, float | None]:
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return False, stdout.strip(), None
    ok = not data.get("is_error", False)
    return ok, str(data.get("result", "")).strip(), data.get("total_cost_usd")


def counted_spend(cfg: Config, records: list[dict]) -> float:
    """Dollars to hold against the daily cap. A Claude call that ended without reporting a
    cost (a timeout, a crash) counts at the per-call cap, the most it can have spent.
    Codex reports no cost at all, so its calls are limited by the call cap only."""
    worst = cfg.budget("agent_usd_per_call")
    return sum(
        worst if r.get("cost_usd") is None and r["engine"] == "claude" else r.get("cost_usd") or 0
        for r in records
    )


def check_budget(cfg: Config) -> None:
    today = registry.from_today(registry.read(cfg.path("ledger")))
    if len(today) >= cfg.budget("agent_calls_per_day"):
        raise BudgetError(f"daily agent-call cap reached ({len(today)} calls today)")
    spent = counted_spend(cfg, today)
    if spent >= cfg.budget("agent_usd_per_day"):
        raise BudgetError(f"daily agent spend cap reached (${spent:.2f} counted today)")


def ask(
    cfg: Config,
    engine: str,
    prompt: str,
    *,
    purpose: str,
    write: bool = False,
    model: str | None = None,
) -> AgentResult:
    """Run one headless agent job, record it in the ledger, and return its final message."""
    check_budget(cfg)
    timeout = cfg.data["engines"]["timeout_s"]
    with tempfile.TemporaryDirectory() as tmp:
        out_file = Path(tmp) / "last_message.txt"
        argv = build_argv(
            engine,
            write=write,
            cwd=cfg.root,
            max_usd=cfg.budget("agent_usd_per_call"),
            out_file=out_file,
            model=model,
        )
        started = time.monotonic()

        def record(ok: bool, cost: float | None) -> float:
            seconds = round(time.monotonic() - started, 1)
            entry = {
                "time": registry.now(),
                "engine": engine,
                "purpose": purpose,
                "write": write,
                "ok": ok,
                "seconds": seconds,
                "cost_usd": cost,
            }
            registry.append(cfg.path("ledger"), entry)
            return seconds

        try:
            code, stdout, stderr = _execute(argv, prompt, cfg.root, timeout)
        except KeyboardInterrupt:
            record(False, None)  # an interrupted call may still have spent money
            raise
        cost = None
        if engine == "claude":
            ok, text, cost = _parse_claude(stdout)
            ok = ok and code == 0
        else:
            text = out_file.read_text().strip() if out_file.is_file() else ""
            ok = code == 0 and bool(text)
    if not ok and not text:
        text = _failure_reason(stdout, stderr)
    seconds = record(ok, cost)
    return AgentResult(engine=engine, ok=ok, text=text, seconds=seconds, cost_usd=cost)
