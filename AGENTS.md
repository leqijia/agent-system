# agent-system

A personal base for doing research and development with coding agents. It holds a small tool,
`lab`, that gives experiments an identity, keeps their artifacts, enforces budgets and runs
independent reviews, plus the notes and conventions that go with it. Claude Code and Codex
both work here and both read this file.

## How work happens

- The repository is the memory. Tasks, decisions, experiment records and reviews are files in
  git. Start every session with `uv run lab status`.
- Work on one task at a time. A task file (`project/tasks/T0001-*.md`) states the goal, how to
  tell it is done, and what may be changed.
- Agents propose, code disposes. A result counts only if `uv run lab run` or the check command
  produced it. Your own summary of what happened is not evidence.
- If a requirement is ambiguous, or a cap or rule blocks you, stop and say so. Do not guess
  and do not work around it.

## Commands

```bash
uv sync                      # install dependencies into .venv
uv run pytest -q             # run the tests (the check command)
uv run ruff check .          # lint
uv run ruff format .         # format
uv run lab status            # where the project stands
uv run lab run experiments/specs/<name>.toml --set key=value   # one experiment
uv run lab runs              # recent experiment records
uv run lab task new "title"  # create a task file
uv run lab review --task T0001   # independent review by the other agent
```

## Map

- `src/labkit/` - the `lab` tool. `experiment.py` is the controller, `agents.py` calls Claude
  Code and Codex headlessly, `review.py` builds review packets.
- `tests/` - tests for the tool.
- `experiments/specs/` - what to run and the limits on it. `runners/` produce raw output,
  `evaluators/` score it. `registry.jsonl` is the record of every run. `runs/` holds logs and
  artifacts and is not committed.
- `project/tasks/`, `project/decisions/`, `project/reviews/`, `project/ledger.jsonl` - the
  work, why choices were made, review verdicts, and a log of headless agent calls.
- `docs/` - the owner's learning notes. Read `docs/03-workflows.md` before proposing a new
  way of working.
- `.claude/skills/` - procedures both agents can load (Codex sees them through
  `.agents/skills`).

## Rules

- Never weaken, skip or delete a test, tolerance, bound or evaluator to make something pass.
- Never edit `lab.toml`, or `max_runs`, `[bounds]` and `[screen]` in an existing spec. Those
  are the owner's decisions. Propose the change instead.
- Never read `data/holdout/`. It exists so that final evaluations stay honest.
- Add dependencies only with `uv add`, and ask first. Never use `pip install`.
- Git: small commits with a clear message. Never force-push, never `git reset --hard`, never
  rewrite history. When a remote exists, push after each major change.
- When `lab` reports a budget cap (exit code 3), stop and report. Do not retry in a loop.
- Runners write raw output to `$LAB_RUN_DIR`; the evaluator writes `metrics.json`. A runner
  never scores itself.

## Learned the hard way

Add a line here the moment something surprising is learned, so the next session of either
agent starts with it.

- `git status --short` hides files inside new folders; use `--untracked-files=all` when the
  full list matters.
- The `codex` on PATH may be much older than the one inside the Codex app, and an old one
  fails with "model is not supported". Check `codex --version` first.
- `claude -p --allowedTools` adds to the project's allow rules; it does not remove tools. A
  read-only headless session needs `--tools "Read,Grep,Glob"`.
- `Bash(uv run *)` in an allow list lets any command through (`uv run git reset --hard`).
  Allow the specific tools instead.
