---
name: map-codebase
description: Get oriented in a large, unfamiliar repository and write a map of it. Use when the user wants to understand, learn from, or start working in a codebase they did not write (for example AlphaFold).
---

# Map a codebase

The goal is a short written map the user can keep, not a tour that scrolls away. Read-only
throughout: change nothing in the repository being studied.

1. **Get it locally.** `git clone --depth 1 <url> ~/Documents/main/reading/<name>`. A local
   copy can be searched; a web page cannot.
2. **Start from the outside.** Read the README, then the build file (`pyproject.toml`,
   `setup.py`, `requirements.txt`, `Dockerfile`) to learn what it depends on and how it runs.
3. **Find the front doors.** Look for entry points: top-level `run_*.py` or `main.py`,
   `[project.scripts]`, `if __name__ == "__main__"`, command definitions. Most repositories
   have only a few.
4. **Trace one real run.** Pick the main entry point and follow one call from the command line
   to the output, writing down each file it passes through. This single path explains more
   than reading folders in order.
5. **Size the parts.** Count files and lines per top-level folder so you know where the weight
   is. Tests, generated files and vendored code are usually skippable.
6. **Read the tests of the part that matters.** Tests show how the authors expect the code to
   be called, with small inputs.
7. **Use history for the why.** `git log --oneline -- <path>` and `git blame` explain choices
   the code does not.
8. **Write the map** to `notes/<name>/MAP.md`:
   - what the project does, in two sentences
   - how to install and run it, and what it needs (data, GPU, services)
   - the path of one run, file by file, with `path:line` references
   - the five to ten files that matter most, one line each
   - the vocabulary: domain terms and what they mean in this code
   - open questions, and what looked surprising or misleading

For a broad search across many files, a subagent keeps the noise out of the main
conversation. For understanding one path in depth, read it yourself.

Check every claim in the map against the code before writing it down. A confident wrong map
is worse than none.
