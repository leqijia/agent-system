---
name: handoff
description: Leave the work in a state the next session can pick up cold, whether that is Claude Code, Codex, or the user tomorrow. Use before ending a session, before clearing context, or before switching engines mid-task.
---

# Handoff

The next session will remember nothing. Everything it needs has to be in the repository.

1. Run `uv run pytest -q` and `uv run lab status` so you describe the real state.
2. In the task file's **Log**, add a dated entry:
   - what was done, as commits or run ids someone can check
   - what was learned, including dead ends, so they are not repeated
   - the exact next step, specific enough to start without re-reading the conversation
   - anything that is broken or half-finished right now
3. Set the task status: `uv run lab task set T0001 doing|review|done`.
4. If something surprising was learned about the tools or the codebase, add one line to
   "Learned the hard way" in `AGENTS.md`.
5. If a choice was made that someone could reasonably question later, record it as a decision
   in `project/decisions/` using the format of the existing ones.
6. Commit with a message that names the task, for example `[T0001] add screening stage`.
   Push if a remote exists.

To pick the work up in the other engine, start it in this folder and say:
"Read project/tasks/T0001-*.md and continue from the last Log entry."
