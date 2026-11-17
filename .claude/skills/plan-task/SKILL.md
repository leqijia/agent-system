---
name: plan-task
description: Turn a rough idea into a task file with a checkable finish line. Use when the user describes work to do and no task file exists yet, or says "plan this" or "new task".
---

# Plan a task

A task is ready when someone with no memory of this conversation could do it and prove it is
done.

1. Interview the user until you could write the task without guessing. Ask about one thing at
   a time: the outcome they want, how they would check it, what must not change, and what
   they have already tried. Stop asking once the answers stop changing the plan.
2. Read the code the task touches before proposing an approach.
3. Create the file: `uv run lab task new "<short title>"`.
4. Fill in every section of the new file:
   - **Goal**: one or two sentences, including why it matters.
   - **Done when**: a command that passes or a result that can be observed. "Works well" is
     not a finish line. `uv run pytest tests/test_x.py` passing is.
   - **Scope**: what may change and what must not.
   - **Notes**: what the user told you that the code does not show.
5. If the task needs more than about a day of work or touches unrelated areas, split it into
   several task files.
6. Show the user the task file and wait for a yes before starting the work. Starting the work
   is a separate step, ideally in a fresh session that reads only the task file.
