# 5. MCP servers and skills worth having

Short version: install few. Each one is somebody else's code or instructions running with
your agent's access, and each adds to what the agent has to keep in mind. Add one when you
notice a specific, repeated need, and remove it if you stop using it.

## What each thing is

| | What it is | When it loads | Typical use |
|---|---|---|---|
| **MCP server** | A program that gives the agent new tools: query a service, drive a browser, read a database | Tool names are listed at session start; the details load when a tool is used | Reaching something outside your folder |
| **Skill** | A folder with a `SKILL.md`: written instructions, sometimes with scripts | Only its one-line description is loaded until the task matches | A procedure you want done the same way each time |
| **Plugin** | A bundle of skills, subagents, hooks and MCP servers installed together | As its parts do | Getting someone's whole setup in one step |

A command-line tool the agent can already run often beats an MCP server. `gh` (GitHub's
command line, already on this machine) covers issues, pull requests and repository contents
with no extra setup, and that is what was used to read commutate and AlphaFold for these
notes.

## MCP servers

Run `/mcp` inside Claude Code to see what is already connected. Connectors you added on
claude.ai (mail, calendar, documents) appear there too.

The three that show up on almost every list of recommendations. I have read the lists, not
tested the servers here, so treat this as "widely recommended", not "verified":

| Server | What it gives the agent | Worth it when |
|---|---|---|
| **Context7** (`upstash/context7`) | Current documentation for a library, by version | The agent keeps writing code for an old version of a package |
| **Playwright** (`microsoft/playwright-mcp`) | A real browser it can click through and screenshot | You build something with a web interface and want it checked visually |
| **GitHub** (`github/github-mcp-server`) | Issues, pull requests, code search | You need more than `gh` offers, or are in a tool without a shell |

For research work specifically, the more useful additions are usually the ones for your own
data: a database server for wherever your results live, or an experiment tracker.

Adding one:

```bash
claude mcp add --transport http <name> <url>     # a hosted server
claude mcp add <name> -- <command to start it>   # a local one
claude mcp list
```

Copy the exact command from the server's own README. To share a server with the project (and
anyone else who clones it), it goes in `.mcp.json` at the repository root; Claude Code asks
before trusting that file. Codex keeps its servers in `~/.codex/config.toml`, so each one has
to be added on both sides if both agents need it.

## Skills

Already in this repository (`.claude/skills/`, shared with Codex):

| Skill | Say something like | What it does |
|---|---|---|
| `plan-task` | "plan a task for …" | Interviews you, then writes a task file with a checkable finish line |
| `experiment-loop` | "tune this", "run an ablation" | Proposes configs, runs them through `lab run`, reads the short summary, stops at the caps |
| `independent-review` | "review this" | Runs `lab review` and acts on the verdict |
| `map-codebase` | "help me understand this repository" | Produces a written map (see note 6) |
| `handoff` | "hand off", "wrap up" | Leaves the task file ready for the next session |

Built into Claude Code and worth using: `/code-review`, `/simplify`, `/security-review`,
`/init`, `/fewer-permission-prompts`, `/loop`, `/schedule`.

From outside, the names that recur in recommendations (same caveat: read about, not tested
here):

| Skill or plugin | What it is |
|---|---|
| **skill-creator** (Anthropic) | Helps you write and test a skill of your own. The most useful one to have, because your own skills fit your work |
| **Superpowers** (`obra/superpowers`) | A plugin of development procedures: brainstorm, plan, test first, debug systematically, review |
| **Document skills** (Anthropic: `docx`, `pdf`, `pptx`, `xlsx`) | Reading and producing office files |
| **frontend-design** (Anthropic) | Better-looking web interfaces |
| **Codex plugin** (`openai/codex-plugin-cc`) | Codex from inside Claude Code (see note 4) |

Several of these are already installed for you; type `/` in a session to see the list.

## Writing your own skill

This is where the real gain is. When you notice you have typed the same instructions three
times, turn them into a skill:

```text
.claude/skills/my-procedure/SKILL.md
```

```markdown
---
name: my-procedure
description: What it does and when to use it. The agent decides from this line alone.
---

Numbered steps, the exact commands, and what to do when something fails.
```

Keep to `name` and `description` in the header so Codex can load it too. Put the trigger
words a person would actually say into the description. Keep it under a page; long skills get
skimmed.

## Before installing anything from a stranger

- **Read it.** A skill is a text file and takes two minutes. An MCP server is a program:
  check who publishes it and whether the repository is active.
- **Prefer the publisher's own server** (GitHub's for GitHub, Microsoft's for Playwright) over
  a look-alike.
- **Content is not instructions.** Anything a tool brings back, a web page, an issue, a
  document, can contain text written to steer the agent. The more a server can reach, the
  more that matters. Give servers read-only access where you can.
- **Fewer is faster.** Every installed tool is something the agent may wrongly reach for.
