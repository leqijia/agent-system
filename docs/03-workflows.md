# 3. Workflows: which one to use when

More agents is not better. Anthropic measured its own multi-agent research system using about
fifteen times the tokens of a chat, and says most coding tasks are a poor fit for it because
the pieces depend on each other. Its advice is to find the simplest thing that works and add
complexity only when it pays. Commutate, which runs six agent roles, has the same rule: "one
agent unless independence or parallelism pays."

So treat the list below as a ladder. Stay on the lowest rung that does the job.

## Rung 1: one agent with a check it can run

Most work belongs here. Give Claude a concrete outcome and a way to verify it.

> Do task T0003. It is done when `uv run pytest tests/test_identity.py` passes.

What makes it work:

- **A finish line that is a command.** The `plan-task` skill writes one into every task file.
- **Say what Claude cannot see**: the symptom, the file, what "fixed" looks like, what you
  already tried.
- **A fresh session per task.** Plan in one session, build in another that reads only the
  task file. Long sessions drift.
- **The stop hook.** Here, Claude cannot finish while lint or tests fail.

## Rung 2: independent review

Use it before calling any task done. An agent grades its own work too kindly; a second agent
that sees only the requirements, the diff and trustworthy evidence does not share its blind
spots.

```bash
uv run lab review --task T0003
```

`lab` runs the tests itself, sends the packet to the other engine in read-only mode, and saves
the verdict in `project/reviews/`. Inside a session you can also say "use the reviewer
subagent on task T0003", or run `/code-review`.

## Rung 3: bounded experimental search

Use it when the work is "try variations and compare": tuning, ablations, benchmarks.

```text
agent proposes a config or code change
        ↓
lab run: validates → screens cheaply → runs → evaluator scores → record appended
        ↓
agent reads a five-line summary and proposes the next change
```

```bash
uv run lab run experiments/specs/my-exp.toml --set lr=0.03
```

What `lab` enforces so the search stays honest and cheap:

| Mechanism | What it prevents |
|---|---|
| Identity = hash of command, config, seed, code files, input files | Paying twice for the same run; confusing two runs that differ |
| `[bounds]` checked first | Spending compute on a config that was never valid |
| `[screen]` stage | A full run of something a short run already shows is broken |
| Separate evaluator writes `metrics.json` | The code under test scoring itself |
| `max_runs` per spec, daily run and compute caps | An unattended loop that never stops |
| `data/holdout/` unreadable by agents | Tuning against the data meant for the final answer |
| Full logs on disk, short summary to the agent | Filling the agent's context with output |

No language model runs during the experiment itself. You pay an agent to think about results,
not to watch a computation.

## Rung 4: parallel sessions in worktrees

Use it when you have two or three changes that truly do not touch the same files.

```bash
claude -w feature-a     # terminal 1: its own folder and branch
claude -w feature-b     # terminal 2
```

Agree shared interfaces first, have one session merge the branches, and run the full checks on
the combined result. Branches that each pass alone can fail together. Two or three parallel
sessions is about what one person can supervise. For a mechanical change across many files,
try the built-in `/batch` before organising it by hand.

## Rung 5: unattended and triggered runs

Use it when a bounded job should start without you: a nightly review, a reaction to a failing
check, a scheduled experiment sweep. Before running anything unattended, answer five
questions: what is the finish condition, how does it check itself, what may it touch, what
stops it, and who signs off.

```bash
uv run lab ask claude "Summarise what changed in experiments/registry.jsonl since yesterday"
uv run lab ask codex --write "Do task T0007 and stop when its Done-when command passes"
```

`lab ask` runs one headless job with a fixed tool list, a spending cap and a ledger entry.
Inside Claude Code, `/loop` repeats a prompt on an interval and `/schedule` runs it in the
cloud on a timetable.

## Rung 6: a workflow engine or the Agent SDK

Not needed yet. Reach for them when the problem changes:

- **A workflow engine such as Prefect** when you have a pipeline of many steps (fetch →
  validate → preprocess → train variants → evaluate → report) and the pain is retries,
  scheduling and not recomputing finished steps. `lab run` becomes one step inside it.
- **The Claude Agent SDK** when you are building an application around the agent: streaming
  progress to your own interface, custom tools, approvals handled by your own code.

## What about subagents, agent teams and dynamic workflows?

- **Subagents** run a side task in a separate context and return a summary. Good for broad
  searches and noisy output. They do not give better answers; they give a cleaner main
  conversation.
- **Dynamic workflows** (say "use a workflow", or the `ultracode` keyword) have Claude write a
  script that fans a job out to many subagents. Good for large audits and research sweeps.
  They use a lot of tokens.
- **Agent teams** are experimental. Several sessions message each other. Use them only when
  workers need to coordinate while working, which is rare.

## Measure before adding machinery

- `/usage` shows where your allowance goes.
- `project/ledger.jsonl` shows what headless calls cost. A one-word answer from `claude -p`
  cost about $0.24 here, because each fresh session reloads its instructions. Many tiny
  headless calls are the expensive way to work; fewer, larger jobs are cheaper.
- Match effort to difficulty: high effort for design and interpreting results, default for
  routine edits.
