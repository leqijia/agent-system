# 4. Using Claude Code and Codex together

The two tools are more alike than different: each is an agent that reads a rules file, loads
skills, runs commands in your folder and can be called without an interactive session. This
repository is arranged so that either one can do any step, and so that the most valuable
combination, one writes and the other reviews, is a single command.

## What they share here

| Thing | Claude Code reads | Codex reads | How this repository keeps one copy |
|---|---|---|---|
| Rules | `CLAUDE.md` | `AGENTS.md` | `CLAUDE.md` is one line, `@AGENTS.md`, plus Claude-only notes |
| Skills | `.claude/skills/` | `.agents/skills/` | `.agents/skills` is a link to `.claude/skills` |
| Tasks, decisions, reviews, run records | files in `project/` and `experiments/` | the same files | Nothing lives in either tool's private memory |

Codex looks for `AGENTS.md` in your home folder (`~/.codex/AGENTS.md`) and then in every
folder from the repository root down to where you started it, and joins them. It stops at 32
KiB by default, which is one more reason to keep the file short.

Rule for both: when either agent learns something surprising, it goes under "Learned the hard
way" in `AGENTS.md`, so the other one starts with it too.

## What they do not share

Text rules are advice to both tools. The hard limits are separate mechanisms, and only Claude
Code's are configured in this repository.

| Guard | Claude Code | Codex |
|---|---|---|
| Refusing force-push, `git reset --hard`, `pip install`, reading `data/holdout/` | Deny rules in `.claude/settings.json`. They stop the named commands, not every roundabout way of doing the same thing | Advice only (written in `AGENTS.md`) |
| Lint and tests run before finishing | The stop hook sends Claude back once, then warns you | Nothing. `lab review` runs the tests itself, so a failure still surfaces |
| `lab status` at session start | Hook | `AGENTS.md` tells it to run the command |
| Limits on where commands can write | Permission mode, optional sandbox | Sandbox mode: `read-only`, `workspace-write` or `danger-full-access` |

In practice: give Codex the reviewing role and bounded, well-specified tasks, and keep work
that touches the protected areas in Claude Code, where the guard rails exist.

## Four ways to combine them

### 1. Cross-review (use this every time)

```bash
uv run lab review --task T0003
```

`lab` runs the tests, collects the diff, and sends both with the task file to the reviewer
named in `lab.toml` (`[engines] reviewer = "codex"`) in read-only mode. The reviewer never
sees the author's explanation. If that engine cannot run, `lab` uses the other one and says so
in the saved review. `--engine claude` or `--engine codex` picks one explicitly.

Why the other engine and not a second session of the same one: models from different
companies make different mistakes, so they are less likely to share a blind spot.

### 2. Codex from inside a Claude Code session

OpenAI publishes a plugin for Claude Code. Install it once, inside Claude Code:

```text
/plugin marketplace add openai/codex-plugin-cc
/plugin install codex@openai-codex
/reload-plugins
/codex:setup
```

| Command | What it does |
|---|---|
| `/codex:review` | Codex reviews your current changes |
| `/codex:adversarial-review` | A review that tries to break the design, not just the code |
| `/codex:rescue` | Hand a stuck problem to Codex |
| `/codex:transfer` | Move the current work over to a Codex session |
| `/codex:status`, `/codex:result`, `/codex:cancel` | Manage Codex jobs running in the background |

The plugin also offers a "review gate" that makes Codex review before Claude may stop
(`/codex:setup --enable-review-gate`). Its own documentation warns that the two agents can
loop and drain your usage. Leave it off; `lab review` gives the same check when you ask for
it.

The plugin and `lab review` overlap. The plugin is convenient mid-conversation. `lab review`
leaves a file in `project/reviews/`, runs the tests itself, and works from either tool or
from no tool at all.

### 3. Handing a task from one to the other

The task file is the handoff. In the tool you are leaving, say "hand off" (the `handoff`
skill writes what was done, what was learned and the exact next step into the task's Log and
commits). In the other tool:

> Read project/tasks/T0003-*.md and continue from the last Log entry.

Useful when one tool is stuck, or when you have run out of allowance on one of them.

### 4. One headless job

```bash
uv run lab ask codex "Explain what src/labkit/identity.py guarantees"      # read-only
uv run lab ask codex --write "Do task T0007; stop when its Done-when command passes"
uv run lab ask claude --write "Do task T0008; stop when its Done-when command passes"
```

Each call is recorded in `project/ledger.jsonl` and counted against the daily caps in
`lab.toml`. Claude Code reports what a call cost; Codex does not, so Codex calls are counted
but not priced. A Claude call that dies without reporting a cost is counted at the per-call
cap, the most it can have spent.

Under the hood these are the two tools' own non-interactive commands:

```bash
claude -p --output-format json --permission-mode dontAsk --tools "Read,Grep,Glob" --strict-mcp-config --max-budget-usd 2
codex exec --sandbox read-only --cd . -          # the prompt arrives on standard input
```

`codex exec` is read-only unless you pass `--sandbox workspace-write`.

## Fix this first on your machine

The `codex` command in your terminal is version 0.42.0, from September 2025. It fails with
"model is not supported when using Codex with a ChatGPT account". The copy inside the ChatGPT
desktop app is current and works. Until the terminal one is updated, `lab review` falls back
to Claude reviewing its own engine's work, which is weaker.

```bash
codex --version
npm install -g @openai/codex@latest
uv run lab status            # the last line shows which engines were found
uv run lab ask codex "Reply with the word ok"
```

## Which one should do what?

Start with the default in `lab.toml`: Claude Code implements, Codex reviews. After a few
weeks, look at `project/reviews/`. If reviews from one engine keep finding real problems and
the other's do not, you have your answer for this kind of work. Swap the two lines under
`[engines]` to try it the other way round.
