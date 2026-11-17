@AGENTS.md

## Claude Code specifics

- Shared rules live in `AGENTS.md` so Codex reads them too. Record new lessons there, under
  "Learned the hard way", not in this file.
- A session-start hook prints `lab status`. A stop hook runs lint and tests when Python files
  have changed and blocks finishing while they fail (`.claude/hooks/stop_check.py`).
- Codex is the default independent reviewer. After finishing a task, run
  `uv run lab review --task <id>` and deal with the findings before calling it done.
- For a second opinion inside this session, use the `reviewer` subagent. It starts with a
  fresh context, so give it the task file path, not your reasoning.
