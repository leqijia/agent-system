# D0002: One instruction file and one skills folder for both agents

Date: 2026-11-16
Status: accepted

## Context

Claude Code reads `CLAUDE.md` and `.claude/skills/`. Codex reads `AGENTS.md` and
`.agents/skills/`. Two copies of the same rules drift apart, and then the two agents behave
differently in the same repository.

## Decision

- `AGENTS.md` is the single source of rules. `CLAUDE.md` imports it with `@AGENTS.md` and adds
  only what is specific to Claude Code.
- Skills live in `.claude/skills/`. `.agents/skills` is a symbolic link to that folder.
- Skill files use only the `name` and `description` fields, which both tools understand.
- Lessons learned go into `AGENTS.md`, whichever agent learned them.

## Alternatives considered

- **Separate files per tool.** Rejected: drift.
- **Only `CLAUDE.md`, with Codex configured to read it** (`project_doc_fallback_filenames`).
  Rejected: it depends on a personal Codex setting that would not travel with the repository.

## Consequences

- Hard limits differ per tool. Claude Code enforces `.claude/settings.json` deny rules and
  hooks. Codex enforces its sandbox mode. Rules written only in `AGENTS.md` are advice to
  both, so anything that must never happen needs a mechanism on each side.
- Claude-only skill features (tool restrictions, dynamic context) are not used in shared
  skills.
