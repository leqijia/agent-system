# 2. How Claude Code is configured, and what it will and will not do

## The one distinction to remember

Everything you can give Claude Code is either **advice** or **enforced**.

- Advice is text Claude reads: `CLAUDE.md`, skills, your prompts. It usually follows it. It can
  also forget it or reason its way around it in a long session.
- Enforced means the program around Claude does it, whatever Claude thinks: permission rules,
  hooks, the sandbox.

Put preferences in advice. Put anything that must always or never happen in something
enforced.

## The layers

| Layer | Where it lives | What it is for | Kind |
|---|---|---|---|
| Project instructions | `CLAUDE.md` (here it imports `AGENTS.md`) | Facts Claude cannot see in the code: commands, rules, traps. Loaded every session, so keep it under about 200 lines | Advice |
| Path rules | `.claude/rules/*.md` | Instructions that apply only to certain folders | Advice |
| Skills | `.claude/skills/<name>/SKILL.md` | A procedure loaded only when the task matches its description. Type `/name` to call one yourself | Advice |
| Subagents | `.claude/agents/<name>.md` | A helper with its own fresh context and its own tool list | Advice, with an enforced tool list |
| Permission rules | `.claude/settings.json` → `permissions` | Which commands run without asking, which ask, which are refused | Enforced |
| Hooks | `.claude/settings.json` → `hooks` | Commands the program runs on events such as session start, before a tool call, or when Claude tries to stop | Enforced |
| MCP servers | `.mcp.json` | Connections to outside tools and data | Tools |
| Personal overrides | `.claude/settings.local.json`, `CLAUDE.local.md` | Your own settings for this project; not committed | - |
| Global | `~/.claude/` (`CLAUDE.md`, `settings.json`, `skills/`, `agents/`) | The same things, applied to every project | - |
| Auto memory | `~/.claude/projects/<project>/memory/` | Notes Claude writes for itself between sessions | Advice |

When to add each one, from Anthropic's own guidance: Claude got the same thing wrong twice →
a line in `CLAUDE.md`. You keep typing the same prompt → a skill. A side task floods the
conversation with output → a subagent. Something must happen every time → a hook. You keep
copying data out of a browser tab → an MCP server.

## What is set up in this repository

- **Allowed without asking**: `uv run`, `uv sync`, reading Git state, `git add`, `git commit`,
  switching branches, worktrees.
- **Always asks**: `uv add`, `uv remove` (a new dependency is your decision).
- **Refused**: force-push, `git reset --hard`, `git clean`, `sudo`, `pip install`, and reading
  `.env` files, `data/holdout/` or `~/.ssh/`.
- **Session-start hook**: runs `lab status` so every session begins knowing the open tasks,
  recent runs and budgets.
- **Stop hook**: if Python files changed, lint and tests must pass before Claude can finish.
- **Subagent**: `reviewer`, for a second opinion inside a session.

## Permission modes

Press `Shift+Tab` in a session to cycle modes. The current one shows under the prompt box.

| Mode | What happens |
|---|---|
| Manual (`default`) | Asks before each file edit and each command |
| Accept edits | Edits files without asking; commands still ask |
| Plan | Reads and proposes a plan; changes nothing until you approve |
| Auto | A safety classifier checks each action. Routine work proceeds; risky actions are blocked or asked about |
| Don't ask (`dontAsk`) | Runs only what the allow rules list and refuses the rest. Meant for unattended runs |
| Bypass (`bypassPermissions`) | No checks. Started with `claude --dangerously-skip-permissions` |

Recent versions start terminal sessions in Auto. Deny rules apply in every mode, including
Bypass.

## Does Claude Code restrict Git?

It depends on where it runs.

- **On your computer (terminal, desktop app, VS Code)**: Git is an ordinary command run with
  your own credentials. Nothing is forbidden by the product itself. What happens is governed
  by the permission mode and your rules. In Auto mode the classifier blocks the destructive
  cases: force-push, `git reset --hard`, discarding uncommitted work, amending commits that
  are already pushed, pointing a remote somewhere new, and merging a pull request nobody
  approved. Ordinary commits and pushes to the current repository go through.
- **In the cloud (claude.ai/code, `claude --cloud`)**: the session runs in a virtual machine
  at Anthropic. Your Git credentials never enter it. Pushes go through a GitHub proxy with
  limited rights, the repository has to be on GitHub, and network access is limited. That is
  where the feeling of "Git is restricted in the app" comes from.

This repository adds its own stricter rules on top (see the Refused list above), because the
commands it refuses are the ones that destroy work.

## Restrictions, and how people reduce them

There are two different things people call restrictions.

**1. The permission system.** This is yours to configure, and loosening it sensibly is normal
practice. From safest to riskiest:

1. Add allow rules for commands you approve constantly. `/fewer-permission-prompts` reads
   your past sessions and proposes a list.
2. Use Auto mode, so routine actions stop asking and only risky ones are checked.
3. Turn on the sandbox (`/sandbox`). The operating system then limits which files and network
   addresses commands can reach, so commands inside those limits can run without prompts.
4. For unattended runs, list exactly what is permitted:
   `claude -p "..." --permission-mode dontAsk --allowedTools "Read,Grep,Bash(uv run *)"`.
   `lab ask` and `lab review` do this for you.
5. `--dangerously-skip-permissions`. People who use it responsibly run it inside a container
   or virtual machine that holds nothing they would mind losing and no credentials. On your
   own laptop with your real files, Auto mode gets most of the benefit without the exposure.

**2. The model's own judgement** about requests that could cause harm. That is not a setting,
and this project does not try to get around it. It is also not what separates beginners from
experts: the productivity gains come from the first list, from good task files, and from
checks the agent can run.

## Commands worth knowing inside a session

| Type this | To do this |
|---|---|
| `Esc` | Interrupt Claude mid-action; your next message redirects it |
| `/rewind` | Go back to an earlier point, restoring files Claude edited |
| `/clear` | Start fresh. Do this between unrelated tasks, and after two failed corrections |
| `/compact focus on X` | Summarise a long conversation, keeping what you name |
| `@path/to/file` | Point Claude at a file |
| `! command` | Run a shell command yourself and share the output |
| `/effort high` | Think harder on a difficult problem (`low`, `medium`, `high`, `xhigh`, `max`) |
| `/usage` | See what you have used |
| `/context` | See what is filling the context window |
| `/code-review` | Review the current changes in a fresh context |
| `/init` | Draft a `CLAUDE.md` for a project that has none |
| `/doctor` | Diagnose installation and configuration problems |

And from the terminal:

| Command | What it does |
|---|---|
| `claude` | Start a session in the current folder |
| `claude --continue` | Reopen the most recent session here |
| `claude --resume` | Choose an earlier session to reopen |
| `claude -w idea-a` | Start a session in a new Git worktree, isolated from your main folder |
| `claude -p "question"` | Ask once and print the answer, with no interactive session |
| `claude --permission-mode plan` | Start in a specific mode |
