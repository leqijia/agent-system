# agent-system

A home base for doing research and development with coding agents (Claude Code and Codex).

It has three parts:

1. **`lab`**, a small command-line tool. It runs experiments so that every result has an
   identity, a record and a budget, and it gets one agent's work reviewed by the other.
2. **Shared agent setup**: one rules file (`AGENTS.md`), five skills, permission rules and two
   hooks, arranged so both agents behave the same way here.
3. **`docs/`**, a short course on the tools underneath: terminal, Git, uv, Claude Code's
   settings and permissions, workflows, MCP servers and skills.

The idea behind all of it, borrowed from [commutate](https://github.com/lucastiger/commutate):
**agents propose, code disposes.** An agent may suggest a change or a config. Whether it
worked is decided by a test or an experiment that ordinary code ran, never by the agent's own
account.

## First ten minutes

Open a terminal in this folder and run these one at a time.

```bash
uv sync                    # install what the project needs into .venv (once)
uv run pytest -q           # run the tests; you should see "21 passed"
uv run lab status          # where the project stands
uv run lab run experiments/specs/example-quadratic.toml               # run an experiment
uv run lab run experiments/specs/example-quadratic.toml               # again: served from cache
uv run lab run experiments/specs/example-quadratic.toml --set lr=0.3  # a variation
uv run lab runs            # everything recorded so far
```

Then start Claude Code here (`claude`) and try: "Read README.md and docs/03-workflows.md, then
walk me through creating my first task."

## The loop for real work

| Step | What you do | What it gives you |
|---|---|---|
| 1. Plan | Ask the agent to "plan a task" (the `plan-task` skill interviews you and writes `project/tasks/T0001-*.md`) | A finish line that can be checked |
| 2. Build | Fresh session: "Do task T0001" | Work judged by tests, not by a summary |
| 3. Experiment | `uv run lab run <spec> --set key=value` (the `experiment-loop` skill) | Cached, capped, recorded runs |
| 4. Review | `uv run lab review --task T0001` | A verdict from an agent that did not write the change |
| 5. Hand off | "Hand off" (the `handoff` skill) updates the task log and commits | The next session, in either tool, starts cold without loss |

## What is in here

```text
AGENTS.md            rules both agents read            CLAUDE.md   imports AGENTS.md
lab.toml             budgets and engine choices (yours to edit, not the agents')
src/labkit/          the lab tool                      tests/      its tests
experiments/
  specs/             what to run and its limits
  runners/           code that produces raw output
  evaluators/        code that scores the output
  registry.jsonl     one line per run, committed
  runs/              logs and artifacts, not committed
project/
  tasks/             one file per task
  decisions/         why things are the way they are
  reviews/           saved review verdicts
  ledger.jsonl       log of headless agent calls and their cost
.claude/             Claude Code settings, hooks, skills, reviewer subagent
.agents/skills       link to .claude/skills, so Codex loads the same skills
docs/                the course
```

## Reading order

1. [Terminal, Git and uv basics](docs/01-terminal-git-uv.md)
2. [How Claude Code is configured, and what it will and will not do](docs/02-claude-code-setup.md)
3. [Workflows: which one to use when](docs/03-workflows.md)
4. [Using Claude Code and Codex together](docs/04-claude-plus-codex.md)
5. [MCP servers and skills worth having](docs/05-mcp-and-skills.md)
6. [Getting to know a large codebase such as AlphaFold](docs/06-reading-a-big-codebase.md)
7. [What commutate teaches, and what not to copy yet](docs/07-what-commutate-teaches.md)

Sources for the claims in these notes are in [docs/sources.md](docs/sources.md).
