---
name: independent-review
description: Get a finished change reviewed by a fresh agent that has not seen how it was made, preferably the other engine (Codex reviews Claude's work and the reverse). Use before calling any task done.
---

# Independent review

The author of a change is the worst judge of it. A reviewer that sees only the requirements,
the diff and evidence it can trust catches what the author talked themselves past.

## Steps

1. Make sure the change is on disk (committed or not) and the task file is up to date.
2. Run the review:

   ```bash
   uv run lab review --task T0001              # uncommitted work, or the last commit
   uv run lab review --task T0001 --base main  # everything on this branch
   ```

   `lab` runs the check command itself, builds the packet, and sends it to a read-only
   session of the engine named in `lab.toml` under `[engines] reviewer`. If that engine
   cannot run, it falls back to the other one and says so. Add `--engine claude` or
   `--engine codex` to choose.
3. Read the saved review in `project/reviews/`.

## Acting on the verdict

- `reject` or any `high` finding: fix it, then review again. Do not argue with the reviewer in
  the task log; change the code or add the missing evidence.
- `accept_with_caveats`: fix the caveats or write them into the task file's Log as known
  limits, then tell the user which you did.
- `cannot_assess`: the requirements or evidence were too thin. Improve the task file's
  "Done when", not the prompt.
- A finding you believe is wrong: reproduce it. If it does not reproduce, say so in the Log
  with the command you ran.

Never run a review more than three times on the same task without talking to the user. A
change that keeps failing review needs a different plan, not another round.
