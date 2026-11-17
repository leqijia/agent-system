# Sources

Gathered on 2026-11-16. These tools change monthly; when a note and the current
documentation disagree, the documentation is right.

## Read directly

These pages or files were opened and read. Claims in the notes that describe how a tool
behaves come from here.

| Source | Used for |
|---|---|
| [Claude Code: best practices](https://code.claude.com/docs/en/best-practices) | Verification as the highest-value habit, plan then build, context management, when to clear (notes 2, 3) |
| [Claude Code: permission modes](https://code.claude.com/docs/en/permission-modes) | The mode table, what Auto mode blocks, deny rules applying in every mode (note 2) |
| [Claude Code: features overview](https://code.claude.com/docs/en/features-overview) | Which layer to use for what; advice versus enforced (note 2) |
| [Claude Code: the `.claude` directory](https://code.claude.com/docs/en/claude-directory) | File locations and what is committed (note 2) |
| [Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web) | Cloud sessions, the GitHub proxy, why Git feels restricted there (note 2) |
| [Claude Code: workflows](https://code.claude.com/docs/en/workflows) | Dynamic workflows and their cost (note 3) |
| [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | "Find the simplest solution"; add complexity only when it pays (note 3) |
| [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) | About fifteen times the tokens of a chat; poor fit for tightly coupled coding (note 3) |
| [Codex: AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Where Codex looks for instructions, the 32 KiB limit (note 4) |
| [Codex: skills](https://learn.chatgpt.com/docs/build-skills) | `.agents/skills`, the shared header fields (notes 4, 5) |
| [Codex: non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode) | `codex exec`, sandbox modes, read-only default (note 4) |
| [openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) (README) | Plugin install steps, commands, the review-gate warning (note 4) |
| [lucastiger/commutate](https://github.com/lucastiger/commutate): `CLAUDE.md`, `.claude/settings.json`, `.claude/agents/critic.md`, `.claude/agents/builder.md`, `.mfos/policy.toml`, `docs/ARCHITECTURE.md`, `project/decisions/D0001-*.md`, and the file tree | Note 7, and the design of this repository |
| [google-deepmind/alphafold](https://github.com/google-deepmind/alphafold): README and directory listings | The layout in note 6 |

## Checked by running it here

| What | Result |
|---|---|
| `claude -p` with the flags `lab` uses | Works. A one-word answer cost about $0.24 |
| `codex exec` on PATH (0.42.0) | Fails: "model is not supported when using Codex with a ChatGPT account" |
| `codex exec` bundled in the ChatGPT app (0.167.0-alpha) with the same flags | Works |
| `lab run`: cache, bounds, screening, caps | Covered by the tests in `tests/` and run by hand |

## Found by search, not read in full

Lower confidence. These shaped the lists of "commonly recommended" tools and a few general
statements; nothing in the notes depends on a detail from them.

| Source | Used for |
|---|---|
| [Anthropic: Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps) | Separating the builder from the evaluator |
| [Anthropic: Claude Code auto mode](https://www.anthropic.com/engineering/claude-code-auto-mode) and [the announcement](https://claude.com/blog/auto-mode) | Background on Auto mode |
| [Onboarding Claude Code like a new developer](https://claude.com/resources/articles/onboarding-claude-code-like-a-new-developer-lessons-from-17-years-of-development) | Codebase orientation habits (note 6) |
| [Simon Willison: Agentic Engineering Patterns](https://simonwillison.net/2026/Feb/23/agentic-engineering-patterns/) | General practice with coding agents |
| [Hugging Face blog: Claude Code skills for 1,000+ ML experiments a day](https://huggingface.co/blog/sionic-ai/claude-code-skills-training) | Skills as the unit of reuse in experiment work |
| [Tips on leveraging AI for empirical research](https://lesswrong.com/posts/f4WZ7dde8KAYHfeif/tips-on-leveraging-ai-for-empirical-research) | Research workflow habits |
| [uv: working on projects](https://docs.astral.sh/uv/guides/projects/) | uv commands (note 1; also verified by using them here) |
| MCP round-ups: [Composio](https://composio.dev/blog/best-mcp-servers-claude-code-codex), [Bannerbear](https://www.bannerbear.com/blog/8-best-mcp-servers-for-claude-code-developers-in-2026/), [Dupple](https://dupple.com/learn/best-mcp-servers-claude-code) | Which servers recur across lists (note 5) |
| Skill round-ups: [Tella](https://www.tella.com/blog/best-claude-code-skills), [Composio](https://composio.dev/content/top-claude-skills), [Artificial Corner](https://artificialcorner.com/p/best-claude-code-skills) | Which skills recur across lists (note 5) |

## Mentioned in the advice you pasted, not read by me

| Source | Why it is here |
|---|---|
| [karpathy/autoresearch](https://github.com/karpathy/autoresearch) | A small example of a bounded experiment loop (rung 3 in note 3) |
| [Prefect](https://www.prefect.io/) | The workflow engine named for rung 6 |
| [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) | For building an application around the agent (rung 6) |
